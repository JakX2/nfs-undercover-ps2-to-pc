"""Fixture-free V55 structural discrimination + optional pinned original Wii scene.

Original game files are never bundled or written; set NFS_UC_WII_SCENE to the
exact locally owned original file to enable source-backed checks.
"""
from __future__ import annotations
import copy
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parent))
import v55_cross_scene_hypothesis_gate as g


def make_scene(n=31,nodes=8,blocks=24,scene_len=68,endian='little',section=0x12345,
               aux=True,tree=True,precull=True,prefix=0x11):
    e=g.endian(endian)
    chunks=[(g.SCENE,struct.pack(e+'I',section)+bytes(scene_len-4))]
    start=8+8+scene_len+8
    pad=(-start)&15
    inst=[]
    for i in range(n):
        row=bytearray(96)
        struct.pack_into(e+'3f',row,0,1.,2.,3.)
        struct.pack_into(e+'3f',row,16,4.,5.,6.)
        struct.pack_into(e+'h',row,28,i%blocks if blocks else 0)
        struct.pack_into(e+'3f',row,32,float(i+1),2.,3.)
        struct.pack_into(e+'h',row,84,0)
        inst.append(row)
    chunks.append((g.INSTANCE,bytes([prefix])*pad+b''.join(inst)))
    if tree: chunks.append((g.TREE,bytes(nodes*48)))
    if precull: chunks.append((g.PRECULL,bytes(blocks*128)))
    if aux: chunks.append((g.AUX,bytes(n*32)))
    payload=b''.join(struct.pack(e+'II',tag,len(data))+data for tag,data in chunks)
    return struct.pack(e+'II',g.ROOT,len(payload))+payload

class SyntheticTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home=Path(self.tmp.name)
        self.ids=0

    def add(self,b,*,label=None,endian='little',hint='wii',offset=None):
        self.ids+=1;label=label or f'case{self.ids}'
        path=self.home/f'{self.ids}.data'
        raw=(b'prefix-for-offset' + b) if offset is not None else b
        if offset is not None:offset=len(b'prefix-for-offset')
        path.write_bytes(raw)
        return {'path':str(path),'label':label,'expected_file_sha256':g.sha256(raw),
                'expected_root_sha256':g.sha256(b),'endian':endian,
                'platform_hint':hint,**({'offset':offset} if offset is not None else {})}

    def test_original_geometry_shape_synthetic_both(self):
        p=g.survey([self.add(make_scene())])['profiles'][0]
        self.assertEqual(p['candidate_96_instance_count'],31)
        self.assertEqual(p['candidate_48_tree_node_count'],8)
        self.assertEqual(p['candidate_128_preculler_block_count'],24)
        self.assertEqual(p['candidate_32_aux_row_count'],31)
        self.assertEqual(p['candidate_96_instance_root_alignment_padding'],4)
        self.assertEqual(list(p['size_hypotheses'].values()),[True,True,True])
        self.assertEqual(p['source_authentication'],'unknown_provenance')

    def test_A_hypothesis_only(self):
        p=g.survey([self.add(make_scene(n=7,nodes=1,blocks=6))])['profiles'][0]
        self.assertTrue(p['size_hypotheses']['length_equals_instance_plus_one_times_96'])
        self.assertFalse(p['size_hypotheses']['length_equals_tree_nodes_times_384'])

    def test_B_hypothesis_only(self):
        p=g.survey([self.add(make_scene(n=3,nodes=3,blocks=9))])['profiles'][0]
        self.assertFalse(p['size_hypotheses']['length_equals_instance_plus_one_times_96'])
        self.assertTrue(p['size_hypotheses']['length_equals_tree_nodes_times_384'])

    def test_neither_hypothesis(self):
        p=g.survey([self.add(make_scene(n=6,nodes=2,blocks=5))])['profiles'][0]
        self.assertFalse(p['size_hypotheses']['length_equals_instance_plus_one_times_96'])
        self.assertFalse(p['size_hypotheses']['length_equals_tree_nodes_times_384'])
        self.assertTrue(p['size_hypotheses']['length_divisible_by_128'])

    def test_repeated_root_deduplicated(self):
        b=make_scene();a=self.add(b);c=self.add(b)
        survey=g.survey([a,c])
        self.assertEqual(survey['submitted_roots'],2)
        self.assertEqual(survey['unique_root_fingerprints'],1)
        self.assertEqual(len(survey['root_labels_repeating_identical_bytes']),1)
        self.assertEqual(survey['candidate_arithmetic_passes_on_distinct_roots']['length_equals_tree_nodes_times_384'],1)
        self.assertFalse(survey['independent_cross_scene_replication_established'])

    def test_modified_root_same_instances_flags(self):
        a=make_scene();b=make_scene(prefix=0x11)
        # Change auxiliary payload byte only, preserving inst stream.
        b=bytearray(b);b[-1]=0x22
        x=g.survey([self.add(a),self.add(bytes(b))])
        self.assertEqual(x['unique_root_fingerprints'],2)
        self.assertEqual(len(x['same_scenery_header_and_instance_payload_groups']),1)
        self.assertFalse(x['new_original_Wii_sectors_authenticated'])

    def test_distinct_synthetic_roots_not_authenticated(self):
        x=g.survey([self.add(make_scene(n=7,nodes=1,blocks=6)),
                    self.add(make_scene(n=3,nodes=3,blocks=9))])
        self.assertEqual(x['unique_root_fingerprints'],2)
        self.assertEqual(x['known_authenticated_Wii_root_count'],0)
        self.assertFalse(x['hypotheses_resolved_for_original_game'])

    def test_offset_accepted(self):
        x=g.survey([self.add(make_scene(),offset=16)])['profiles'][0]
        self.assertEqual(x['stream_offset'],len(b'prefix-for-offset'))

    def test_big_endian_structural_only(self):
        x=g.survey([self.add(make_scene(endian='big'),endian='big',hint='carbon_pc')])['profiles'][0]
        self.assertEqual(x['candidate_96_instance_count'],31)
        self.assertFalse(x['candidate_wii_schema_is_PC_serialization_proof'])
        self.assertEqual(x['source_authentication'],'unknown_provenance')

    def test_padding_changes_with_absolute_root_header(self):
        for extra in (0,4,8,12):
            with self.subTest(extra=extra):
                x=g.survey([self.add(make_scene(scene_len=68+extra))])['profiles'][0]
                self.assertEqual(x['candidate_96_instance_root_alignment_padding'],(4-extra)%16)
                self.assertEqual(x['candidate_96_instance_count'],31)

    def test_zero_instances_not_accepted_as_runtime_proof(self):
        x=g.survey([self.add(make_scene(n=0,nodes=1,blocks=3))])['profiles'][0]
        self.assertEqual(x['candidate_96_instance_count'],0)
        self.assertFalse(x['runtime_compatibility_verified'])

    def test_source_file_sha_guard(self):
        x=self.add(make_scene());x['expected_file_sha256']='a'*64
        with self.assertRaisesRegex(g.GateError,'file fingerprint mismatch'):g.survey([x])

    def test_root_sha_guard(self):
        x=self.add(make_scene());x['expected_root_sha256']='b'*64
        with self.assertRaisesRegex(g.GateError,'root fingerprint mismatch'):g.survey([x])

    def test_malformed_sha_rejected(self):
        x=self.add(make_scene());x['expected_root_sha256']='z'*64
        with self.assertRaises(g.GateError):g.survey([x])

    def test_missing_path_rejected(self):
        x=self.add(make_scene());x['path']=str(self.home/'missing.file')
        with self.assertRaises(g.GateError):g.survey([x])

    def test_bad_endian_rejected(self):
        x=self.add(make_scene());x['endian']='native'
        with self.assertRaises(g.GateError):g.survey([x])

    def test_bad_hint_rejected(self):
        x=self.add(make_scene());x['platform_hint']='proven_pc'
        with self.assertRaises(g.GateError):g.survey([x])

    def test_bad_offset_rejected(self):
        x=self.add(make_scene());x['offset']=999999999
        with self.assertRaises(g.GateError):g.survey([x])

    def test_boolean_offset_rejected(self):
        x=self.add(make_scene());x['offset']=True
        with self.assertRaises(g.GateError):g.survey([x])

    def test_offset_wrong_header_rejected(self):
        x=self.add(make_scene());x['offset']=4
        with self.assertRaises(g.GateError):g.survey([x])

    def test_duplicate_child_rejected(self):
        b=make_scene();e='<';extra=struct.pack(e+'II',g.SCENE,4)+b'\x00'*4
        b=struct.pack(e+'II',g.ROOT,len(b)+len(extra)-8)+b[8:]+extra
        with self.assertRaisesRegex(g.GateError,'duplicate'):g.survey([self.add(b)])

    def test_child_overflow_rejected(self):
        b=bytearray(make_scene());struct.pack_into('<I',b,8+4,0x7fffffff)
        with self.assertRaises(g.GateError):g.survey([self.add(bytes(b))])

    def test_missing_mandatory_instance(self):
        b=make_scene()
        # Replace INSTANCE child ID with a valid unknown, preserving framing.
        b=bytearray(b);struct.pack_into('<I',b,8+8+68,0x34120)
        with self.assertRaisesRegex(g.GateError,'missing'):g.survey([self.add(bytes(b))])

    def test_incomplete_instance_stride_candidate(self):
        b=make_scene();parts=g.children(b,'little');instance_start,payload=parts[g.INSTANCE]
        # Change padding or row size by altering content AND valid framed headers.
        p=instance_start-8
        broken=b[:p]+struct.pack('<II',g.INSTANCE,len(payload)+1)+payload+b'\xff'+b[p+8+len(payload):]
        broken=struct.pack('<II',g.ROOT,len(broken)-8)+broken[8:]
        report=g.survey([self.add(broken)])['profiles'][0]
        self.assertIsNone(report['candidate_96_instance_count'])
        self.assertFalse(report['size_hypotheses']['length_equals_instance_plus_one_times_96'])

    def test_missing_optional_tree_and_precull(self):
        p=g.survey([self.add(make_scene(tree=False,precull=False))])['profiles'][0]
        self.assertIsNone(p['candidate_48_tree_node_count'])
        self.assertIsNone(p['candidate_128_preculler_block_count'])
        self.assertFalse(p['size_hypotheses']['length_divisible_by_128'])

    def test_wrong_preculler_stride_rejected_as_candidate_only(self):
        b=make_scene();start,payload=g.children(b,'little')[g.PRECULL]
        head=start-8
        broken=b[:head]+struct.pack('<II',g.PRECULL,len(payload)+1)+payload+b'\x00'+b[start+len(payload):]
        broken=struct.pack('<II',g.ROOT,len(broken)-8)+broken[8:]
        p=g.survey([self.add(broken)])['profiles'][0]
        self.assertIsNone(p['candidate_128_preculler_block_count'])

    def test_duplicate_label_rejected(self):
        with self.assertRaisesRegex(g.GateError,'duplicate report label'):
            g.survey([self.add(make_scene(),label='x'),self.add(make_scene(),label='x')])

    def test_duplicate_or_missing_specs_rejected(self):
        with self.assertRaises(g.GateError):g.survey([])
        with self.assertRaises(g.GateError):g.survey([{}])

    def test_manifest_input_not_disclosed_in_report(self):
        x=self.add(make_scene());report=g.survey([x]);text=json.dumps(report)
        self.assertNotIn(str(self.home),text)
        self.assertNotIn(x['path'],text)

    def test_cli_report_and_source_immutable(self):
        x=self.add(make_scene());manifest=self.home/'manifest.json';out=self.home/'summary.json'
        manifest.write_text(json.dumps({'roots':[x]}))
        before=Path(x['path']).read_bytes()
        call=subprocess.run([sys.executable,str(Path(g.__file__)),'--manifest',str(manifest),
                             '--report',str(out)],capture_output=True,text=True)
        self.assertEqual(call.returncode,0,call.stderr)
        self.assertEqual(Path(x['path']).read_bytes(),before)
        self.assertEqual(json.loads(out.read_text())['submitted_roots'],1)
        call2=subprocess.run([sys.executable,str(Path(g.__file__)),'--manifest',str(manifest),
                             '--report',str(out)],capture_output=True,text=True)
        self.assertNotEqual(call2.returncode,0)

    def test_cli_reject_source_overwrite(self):
        x=self.add(make_scene());manifest=self.home/'manifest.json'
        manifest.write_text(json.dumps([x]))
        z=subprocess.run([sys.executable,str(Path(g.__file__)),'--manifest',str(manifest),
                          '--report',x['path']],capture_output=True,text=True)
        self.assertNotEqual(z.returncode,0)
        self.assertIn('overwrite',z.stderr.lower())

    def test_cli_wrong_sha_does_not_leave_report(self):
        x=self.add(make_scene());x['expected_root_sha256']='0'*64
        manifest=self.home/'manifest.json';out=self.home/'out.json'
        manifest.write_text(json.dumps({'roots':[x]}))
        z=subprocess.run([sys.executable,str(Path(g.__file__)),'--manifest',str(manifest),
                          '--report',str(out)],capture_output=True,text=True)
        self.assertNotEqual(z.returncode,0);self.assertFalse(out.exists())

    def test_negative_and_invalid_refs_remain_caution(self):
        b=bytearray(make_scene(n=3,nodes=1,blocks=1))
        start,payload=g.children(b,'little')[g.INSTANCE]
        pad=(-start)&15
        struct.pack_into('<h',b,start+pad+28,-1)
        struct.pack_into('<h',b,start+pad+96+28,22)
        x=g.survey([self.add(bytes(b))])['profiles'][0]['candidate_preculler_ref_statistics']
        self.assertEqual(x['negative_count'],1)
        self.assertEqual(x['out_of_candidate_block_range'],1)

    def test_unique_root_count_cap_and_type(self):
        with self.assertRaises(g.GateError):g.survey('bad')
        with self.assertRaises(g.GateError):g.survey([{}]*257)

class OriginalWiiFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p=os.environ.get('NFS_UC_WII_SCENE')
        if not p:raise unittest.SkipTest('NFS_UC_WII_SCENE not supplied; proprietary original Wii fixture excluded')
        cls.path=Path(p)
        if not cls.path.is_file():raise AssertionError('Explicit fixture path missing')
        cls.sha=g.file_digest(cls.path)
        if cls.sha!=g.WII_REDBUILDING_SHA:raise AssertionError('Explicit fixture does not match pinned original source')
        cls.r=g.survey([{'path':str(cls.path),'label':'original_wii_root',
                         'expected_file_sha256':cls.sha,'expected_root_sha256':cls.sha,
                         'platform_hint':'wii','endian':'little'}])
        cls.profile=cls.r['profiles'][0]

    def test_known_original_provenance(self):
        self.assertEqual(self.profile['source_authentication'],'known_exact_original_Wii_RedBuilding')
    def test_original_counts(self):
        self.assertEqual((self.profile['candidate_96_instance_count'],self.profile['candidate_48_tree_node_count'],
                          self.profile['candidate_128_preculler_block_count'],self.profile['candidate_32_aux_row_count']),
                          (31,8,24,31))
    def test_both_hypotheses_fit_original(self):
        self.assertTrue(self.profile['size_hypotheses']['length_equals_instance_plus_one_times_96'])
        self.assertTrue(self.profile['size_hypotheses']['length_equals_tree_nodes_times_384'])
    def test_all_24_candidate_preculler_blocks_referenced(self):
        self.assertEqual(self.profile['candidate_preculler_ref_statistics']['referenced_nonnegative_distinct_count'],24)
    def test_original_alignment_and_child_lengths(self):
        self.assertEqual(self.profile['candidate_96_instance_root_alignment_padding'],4)
        self.assertEqual((self.profile['child_lengths']['0x34103'],self.profile['child_lengths']['0x34107']),
                         (2980,3072))
    def test_original_does_not_prove_replication_or_carbon_abi(self):
        self.assertEqual(self.r['known_authenticated_Wii_root_count'],1)
        self.assertFalse(self.r['independent_cross_scene_replication_established'])
        self.assertFalse(self.r['carbon_pc_serialized_0x34107_proven'])
    def test_duplicate_known_file_does_not_count_twice(self):
        x={'path':str(self.path),'label':'a','expected_file_sha256':self.sha,
           'expected_root_sha256':self.sha,'endian':'little','platform_hint':'wii'}
        y=dict(x,label='b')
        r=g.survey([x,y]);self.assertEqual(r['known_authenticated_Wii_root_count'],1)
        self.assertEqual(r['unique_root_fingerprints'],1)

if __name__=='__main__':unittest.main()