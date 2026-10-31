"""V60 candidate streaming index cross-anchor checks (only synthetic fixtures in CI)."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0,str(Path(__file__).resolve().parent))
import v60_multi_anchor_index_gate as m

WII_SHA=m.v55.WII_REDBUILDING_SHA


def digest(b):return hashlib.sha256(b).hexdigest()


def child(tag,payload):return struct.pack('<II',tag,len(payload))+payload


def root(seed):
    payload=child(m.v55.SCENE,struct.pack('<I',seed))+child(m.v55.INSTANCE,b'X'*96)
    return struct.pack('<II',m.v55.ROOT,len(payload))+payload


def make_master(offsets,stride=92,field=20,at=24, extra_fields=()):
    rows=bytearray(stride*len(offsets))
    for i,value in enumerate(offsets):
        struct.pack_into('<I',rows,i*stride+field,value)
        for other in extra_fields:struct.pack_into('<I',rows,i*stride+other,value)
    return b'A'*at+struct.pack('<II',m.v59.TABLE,len(rows))+rows+b'TAIL'


class V60Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name)
        self.a=root(111);self.b=root(222)
        self.offsets=[128,512]
        self.stream=b'P'*128+self.a+b'Q'*(512-128-len(self.a))+self.b+b'S'*60
        self.master=make_master([16,128,512,1024])
        self.save('stream.bin',self.stream);self.save('master.bin',self.master)

    def save(self,name,data):
        (self.base/name).write_bytes(data)

    def manifest(self,roots=None,hypotheses=None):
        if roots is None:roots=[(str(i),at,b) for i,(at,b) in enumerate(zip(self.offsets,[self.a,self.b]))]
        return {'stream':{'path':str(self.base/'stream.bin'),'expected_file_sha256':digest(self.stream),'endian':'little'},
                'master':{'path':str(self.base/'master.bin'),'expected_file_sha256':digest(self.master),
                          'chunk_header_offset':24,'endian':'little'},
                'roots':[{'label':label,'offset':off,'expected_root_sha256':digest(raw)} for label,off,raw in roots],
                'hypotheses':hypotheses if hypotheses is not None else [self.h()]}

    def h(self,id='h',stride=92,count=4,field=20,base=0):
        return {'id':id,'row_stride':stride,'row_count':count,'offset_field':field,'offset_base':base}

    def test_full_multiple_unique_match(self):
        r=m.evaluate_layouts(self.manifest())
        x=r['candidate_layouts'][0]
        self.assertEqual(x['uniquely_matched_anchor_count'],2)
        self.assertEqual(x['uniquely_matched_distinct_root_sha_count'],2)
        self.assertEqual(x['anchor_matches'][0]['matching_candidate_rows'],[1])
        self.assertEqual(x['anchor_matches'][1]['matching_candidate_rows'],[2])
        self.assertEqual(x['structural_status'],'multiple_distinct_roots_structurally_match_NOT_loader_proof')

    def test_large_source_files_are_hashed_once_each(self):
        original=m.v55.file_digest
        with mock.patch.object(m.v55,'file_digest', wraps=original) as wrapped:
            m.evaluate_layouts(self.manifest(hypotheses=[self.h('a'),self.h('b',field=24)]))
        self.assertEqual(wrapped.call_count,2)

    def test_bool_row_stride_rejected_without_false_match(self):
        r=m.evaluate_layouts(self.manifest(hypotheses=[self.h('invalid',stride=True)]))
        self.assertEqual(r['candidate_layouts'][0]['structural_status'],'layout_rejected')

    def test_malformed_root_label_rejected(self):
        data=self.manifest();data['roots'][0]['label']=''
        with self.assertRaises(m.GateError):m.evaluate_layouts(data)

    def test_never_proves_carbon_abi(self):
        r=m.evaluate_layouts(self.manifest())
        self.assertFalse(r['carbon_PC_master_index_semantics_proven'])
        self.assertFalse(r['native_Carbon_loader_and_relocations_verified'])
        self.assertFalse(r['safe_to_install'])
        self.assertFalse(r['multiple_distinct_original_carbon_PC_roots_authenticated'])

    def test_single_anchor_does_not_establish_multi(self):
        r=m.evaluate_layouts(self.manifest(roots=[('a',128,self.a)]))
        self.assertEqual(r['candidate_layouts'][0]['structural_status'],'single_distinct_root_structural_match_only')

    def test_identical_root_bytes_at_different_offsets_not_independent_structure(self):
        self.b=self.a
        self.stream=b'P'*128+self.a+b'Q'*(512-128-len(self.a))+self.b+b'S'*60
        self.save('stream.bin',self.stream)
        r=m.evaluate_layouts(self.manifest())
        self.assertEqual(r['source_root_count'],2)
        self.assertEqual(r['distinct_root_payload_sha_count'],1)
        self.assertEqual(r['candidate_layouts'][0]['structural_status'],'single_distinct_root_structural_match_only')

    def test_no_contenders_when_root_anchor_unmatched(self):
        self.master=make_master([16,128,888,1024]);self.save('master.bin',self.master)
        r=m.evaluate_layouts(self.manifest())
        self.assertEqual(r['layouts_matching_all_root_anchors'],[])
        self.assertFalse(r['layout_ambiguity_flag'])

    def test_missing_anchor_is_contradiction(self):
        self.master=make_master([16,128,888,1024]);self.save('master.bin',self.master)
        x=m.evaluate_layouts(self.manifest())['candidate_layouts'][0]
        self.assertEqual(x['structural_status'],'anchor_contradiction_or_ambiguity')
        self.assertEqual(x['uniquely_matched_anchor_count'],1)

    def test_duplicate_index_row_is_ambiguous(self):
        self.master=make_master([128,128,512,1024]);self.save('master.bin',self.master)
        x=m.evaluate_layouts(self.manifest())['candidate_layouts'][0]
        self.assertEqual(x['anchor_matches'][0]['matching_candidate_rows'],[0,1])
        self.assertFalse(x['all_anchors_uniquely_matched'])

    def test_two_valid_field_hypotheses_are_reported_ambiguous(self):
        self.master=make_master([16,128,512,1024],extra_fields=[24]);self.save('master.bin',self.master)
        r=m.evaluate_layouts(self.manifest(hypotheses=[self.h('a'),self.h('b',field=24)]))
        self.assertTrue(r['layout_ambiguity_flag'])
        self.assertEqual(r['layouts_matching_all_root_anchors'],['a','b'])

    def test_different_field_hypothesis_rejected_by_anchor(self):
        r=m.evaluate_layouts(self.manifest(hypotheses=[self.h('wrong',field=24)]))
        self.assertEqual(r['candidate_layouts'][0]['structural_status'],'anchor_contradiction_or_ambiguity')

    def test_wrong_row_stride_rejected(self):
        r=m.evaluate_layouts(self.manifest(hypotheses=[self.h('wrong',stride=88)]))
        self.assertEqual(r['candidate_layouts'][0]['structural_status'],'layout_rejected')

    def test_wrong_row_count_rejected(self):
        r=m.evaluate_layouts(self.manifest(hypotheses=[self.h('wrong',count=3)]))
        self.assertEqual(r['candidate_layouts'][0]['structural_status'],'layout_rejected')

    def test_wrong_field_outside_row_rejected(self):
        r=m.evaluate_layouts(self.manifest(hypotheses=[self.h(field=92)]))
        self.assertEqual(r['candidate_layouts'][0]['structural_status'],'layout_rejected')

    def test_candidate_offset_base(self):
        self.master=make_master([0,28,412,900]);self.save('master.bin',self.master)
        r=m.evaluate_layouts(self.manifest(hypotheses=[self.h(base=100)]))
        self.assertTrue(r['candidate_layouts'][0]['all_anchors_uniquely_matched'])

    def test_offset_base_wrong_is_contradiction(self):
        r=m.evaluate_layouts(self.manifest(hypotheses=[self.h(base=1)]))
        self.assertFalse(r['candidate_layouts'][0]['all_anchors_uniquely_matched'])

    def test_root_interior_rows_flagged(self):
        self.master=make_master([129,128,512,1024]);self.save('master.bin',self.master)
        x=m.evaluate_layouts(self.manifest())['candidate_layouts'][0]
        self.assertEqual(x['anchor_matches'][0]['candidate_rows_pointing_inside_root_not_at_start'],1)

    def test_duplicate_root_start_rejected(self):
        data=self.manifest();data['roots'].append(dict(data['roots'][0],label='duplicate'))
        with self.assertRaises(m.GateError):m.evaluate_layouts(data)

    def test_duplicate_label_rejected(self):
        data=self.manifest();data['roots'][1]['label']='0'
        with self.assertRaises(m.GateError):m.evaluate_layouts(data)

    def test_overlapping_roots_rejected(self):
        # Use a valid nested framed root at byte 160, inside the enclosing first root.
        # The input can never legitimately be counted as two disjoint source anchors.
        b=bytearray(self.stream); b[160:160+len(self.b)]=self.b
        self.stream=bytes(b);self.save('stream.bin',self.stream)
        data=self.manifest(roots=[('a',128,self.a),('b',160,self.b)])
        data['roots'][0]['expected_root_sha256']=digest(self.stream[128:128+len(self.a)])
        with self.assertRaises(m.GateError):m.evaluate_layouts(data)

    def test_root_hash_guard(self):
        data=self.manifest();data['roots'][0]['expected_root_sha256']='0'*64
        with self.assertRaises(m.GateError):m.evaluate_layouts(data)

    def test_stream_hash_guard(self):
        data=self.manifest();data['stream']['expected_file_sha256']='0'*64
        with self.assertRaises(m.GateError):m.evaluate_layouts(data)

    def test_master_hash_guard(self):
        data=self.manifest();data['master']['expected_file_sha256']='0'*64
        with self.assertRaises(m.GateError):m.evaluate_layouts(data)

    def test_invalid_stream_master_endian_mismatch(self):
        data=self.manifest();data['master']['endian']='big'
        with self.assertRaises(m.GateError):m.evaluate_layouts(data)

    def test_invalid_root_offset_bool(self):
        data=self.manifest();data['roots'][0]['offset']=True
        with self.assertRaises(m.GateError):m.evaluate_layouts(data)

    def test_duplicate_hypothesis_id(self):
        data=self.manifest(hypotheses=[self.h('a'),self.h('a',field=24)])
        with self.assertRaises(m.GateError):m.evaluate_layouts(data)

    def test_no_roots_fails_closed(self):
        data=self.manifest();data['roots']=[]
        with self.assertRaises(m.GateError):m.evaluate_layouts(data)

    def test_no_layouts_fails_closed(self):
        data=self.manifest();data['hypotheses']=[]
        with self.assertRaises(m.GateError):m.evaluate_layouts(data)

    def test_too_many_anchors_fails_closed(self):
        data=self.manifest();data['roots']=data['roots']*33
        with self.assertRaises(m.GateError):m.evaluate_layouts(data)

    def test_too_many_hypotheses_fails_closed(self):
        data=self.manifest();data['hypotheses']=[self.h(str(i)) for i in range(65)]
        with self.assertRaises(m.GateError):m.evaluate_layouts(data)

    def test_invalid_master_chunk_tag_rejects_layout(self):
        self.master=b'A'*24+b'XXXXXXXX'+self.master[32:];self.save('master.bin',self.master)
        r=m.evaluate_layouts(self.manifest())
        self.assertEqual(r['candidate_layouts'][0]['structural_status'],'layout_rejected')

    def test_output_excludes_local_paths(self):
        report=json.dumps(m.evaluate_layouts(self.manifest()))
        self.assertNotIn(str(self.base),report)
        self.assertNotIn('stream.bin',report)
        self.assertNotIn('master.bin',report)

    def test_cli_creates_new_report(self):
        manifest=self.base/'manifest.json';out=self.base/'report.json'
        manifest.write_text(json.dumps(self.manifest()),encoding='utf-8')
        proc=subprocess.run([sys.executable,str(Path(m.__file__)),'--manifest',str(manifest),'--report',str(out)],capture_output=True,text=True)
        self.assertEqual(proc.returncode,0,proc.stderr)
        self.assertFalse(json.loads(out.read_text())['safe_to_install'])

    def test_cli_refuses_overwrite(self):
        manifest=self.base/'manifest.json';manifest.write_text(json.dumps(self.manifest()),encoding='utf-8')
        out=self.base/'master.bin'
        proc=subprocess.run([sys.executable,str(Path(m.__file__)),'--manifest',str(manifest),'--report',str(out)],capture_output=True,text=True)
        self.assertNotEqual(proc.returncode,0)
        self.assertEqual(out.read_bytes(),self.master)

    def test_header_offset_wrong_rejects_layout(self):
        data=self.manifest();data['master']['chunk_header_offset']=0
        self.assertEqual(m.evaluate_layouts(data)['candidate_layouts'][0]['structural_status'],'layout_rejected')

    def test_file_missing_fails_closed(self):
        data=self.manifest();data['stream']['path']=str(self.base/'MISSING')
        with self.assertRaises(m.GateError):m.evaluate_layouts(data)


class V60OriginalWiiFixtureTests(unittest.TestCase):
    """Only run when exact original copyrighted scene is explicitly available locally."""
    def setUp(self):
        source=os.environ.get('NFS_UC_WII_SCENE')
        if not source: self.skipTest('Original Wii fixture not supplied in public CI')
        blob=Path(source).read_bytes()
        if digest(blob)!=WII_SHA: self.skipTest('Not exact original Wii RedBuilding scene')
        self.wii=blob
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name)
        self.fake=root(234)
        self.start=256;self.next=9000
        self.stream=b'P'*self.start+self.wii+b'X'*(self.next-self.start-len(self.wii))+self.fake+b'S'*18
        self.master=make_master([20,self.start,self.next,10100])
        (self.base/'stream').write_bytes(self.stream)
        (self.base/'master').write_bytes(self.master)
    def manifest(self,only_original=False):
        roots=[{'label':'wii_original','offset':self.start,'expected_root_sha256':WII_SHA}]
        if not only_original:
            roots.append({'label':'synthetic_scene_not_original','offset':self.next,'expected_root_sha256':digest(self.fake)})
        return {'stream':{'path':str(self.base/'stream'),'expected_file_sha256':digest(self.stream),'endian':'little'},
                'master':{'path':str(self.base/'master'),'expected_file_sha256':digest(self.master),
                          'chunk_header_offset':24,'endian':'little'},
                'roots':roots,'hypotheses':[{'id':'illustrative_not_Carbon','row_stride':92,'row_count':4,'offset_field':20}]}
    def test_exact_original_root_sha(self):
        self.assertEqual(digest(self.wii),WII_SHA)
    def test_original_only_is_insufficient(self):
        r=m.evaluate_layouts(self.manifest(only_original=True))
        self.assertEqual(r['candidate_layouts'][0]['structural_status'],'single_distinct_root_structural_match_only')
    def test_original_plus_synthetic_not_authenticated_Carbon(self):
        r=m.evaluate_layouts(self.manifest())
        self.assertEqual(r['candidate_layouts'][0]['uniquely_matched_distinct_root_sha_count'],2)
        self.assertFalse(r['multiple_distinct_original_carbon_PC_roots_authenticated'])
        self.assertFalse(r['safe_to_install'])
    def test_wii_original_expected_hash_guard_rejects(self):
        data=self.manifest();data['roots'][0]['expected_root_sha256']='0'*64
        with self.assertRaises(m.GateError):m.evaluate_layouts(data)
    def test_fixture_not_leaked_to_json(self):
        r=json.dumps(m.evaluate_layouts(self.manifest()))
        self.assertNotIn(str(self.base),r)
        self.assertNotIn('synthetic_scene_not_original.chunks',r)

if __name__=='__main__':unittest.main()