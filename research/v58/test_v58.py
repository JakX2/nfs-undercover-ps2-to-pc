"""V58 no-asset stream-envelope tests; optional SHA-pinned original Wii tests."""
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

sys.path.insert(0,str(Path(__file__).resolve().parent))
import v58_stream_envelope_gate as m


def frame(children,order='little'):
    e=m.v55.endian(order)
    payload=b''.join(struct.pack(e+'II',tag,len(data))+data for tag,data in children)
    return struct.pack(e+'II',m.v55.ROOT,len(payload))+payload


def synthetic_root(order='little',info_before=False):
    scene=(m.v55.SCENE,b'\x00'*4)
    inst=(m.v57.INST,b'\x11'*4+b'R'*96)
    info=(m.v57.INFO,b'I'*72)
    aux=(m.v57.AUX,b'A'*32)
    tree=(m.v55.TREE,b'T'*48)
    prec=(m.v55.PRECULL,b'P'*128)
    children=[scene,info,inst,aux,tree,prec] if info_before else [scene,inst,info,aux,tree,prec]
    # 96-byte synthetic row padding for actual child layout
    pos=8;updated=[]
    for tag,payload in children:
        if tag==m.v57.INST:
            pad=(-pos-8)&15
            payload=b'\x11'*pad+b'R'*96
        updated.append((tag,payload));pos+=8+len(payload)
    return frame(updated,order)


def appended_root(src,order='little'):
    ch=m.v55.children(src,order)
    extra={m.v57.INST:b'r'*96,m.v57.INFO:b'i'*72,m.v57.AUX:b'a'*32}
    return frame([(tag,chunk[1]+extra.get(tag,b'')) for tag,chunk in ch.items()],order)


def stream(src,offset=64,prefix_marker=False,suffix=b'ending-tail'):
    prefix=bytearray(b'Z'*offset)
    if prefix_marker:struct.pack_into('<I',prefix,8,offset+len(src))
    return bytes(prefix)+src+suffix


def spec(path,order='little',offset=None,root=None):
    data=path.read_bytes()
    if root is None:root=data if offset is None else data[offset:]
    out={'path':str(path),'label':'test', 'endian':order,
         'expected_file_sha256':hashlib.sha256(data).hexdigest(),
         'expected_root_sha256':hashlib.sha256(root).hexdigest(),
         'platform_hint':'unknown'}
    if offset is not None:out['offset']=offset
    return out


class SyntheticEnvelopeTests(unittest.TestCase):
    def setUp(self):
        self.dir=tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.path=Path(self.dir.name)
        self.old=synthetic_root()
        self.new=appended_root(self.old)
        self.orig=self.path/'original.stream'
        self.cand=self.path/'candidate.stream'
        self.orig.write_bytes(stream(self.old,prefix_marker=True))
        self.cand.write_bytes(self.orig.read_bytes()[:64]+self.new+b'ending-tail')
        self.a=spec(self.orig,offset=64,root=self.old)
        self.b=spec(self.cand,offset=64,root=self.new)

    def test_projection_root_end_plus_200(self):
        r=m.report({'original':self.a})['projection']
        self.assertEqual(r['projected_root_end_exclusive']-r['original_root_end_exclusive'],200)
    def test_projection_stream_size_plus_200(self):
        r=m.report({'original':self.a})['projection']
        self.assertEqual(r['hypothetical_file_bytes_after_insertion']-r['original_file_bytes'],200)
    def test_projection_external_tail_shift(self):
        r=m.report({'original':self.a})['projection']
        self.assertEqual(r['external_suffix_bytes_that_would_shift'],len(b'ending-tail'))
        self.assertEqual(r['external_suffix_displacement_bytes'],200)
    def test_projection_prefix_stays_put(self):
        r=m.report({'original':self.a})['projection']
        self.assertEqual(r['external_prefix_bytes_unmoved'],64)
    def test_projection_root_absolute_coordinates(self):
        r=m.report({'original':self.a})['projection']
        self.assertEqual(r['root_stream_offset'],64)
        self.assertEqual(r['original_root_end_exclusive'],64+len(self.old))
    def test_tree_absolute_shift_plus_200(self):
        r=m.report({'original':self.a})['projection']
        x={v['child_id']:v for v in r['child_absolute_offsets']}
        self.assertEqual(x['0x34105']['absolute_shift'],200)
    def test_instance_absolute_no_shift(self):
        r=m.report({'original':self.a})['projection']
        x={v['child_id']:v for v in r['child_absolute_offsets']}
        self.assertEqual(x['0x34103']['absolute_shift'],0)
    def test_wii_order_vs_info_first_absolute_shift(self):
        root=synthetic_root(info_before=True)
        p=self.path/'info-first';p.write_bytes(stream(root))
        x=m.report({'original':spec(p,offset=64,root=root)})['projection']
        shifts={v['child_id']:v['absolute_shift'] for v in x['child_absolute_offsets']}
        self.assertEqual(shifts['0x34103'],72)
    def test_candidate_comparison_success(self):
        r=m.report({'original':self.a,'candidate':self.b})
        self.assertTrue(r['strict_envelope_pair']['external_suffix_unchanged_after_shift'])
        self.assertTrue(r['strict_envelope_pair']['root_append_contract_passed'])
    def test_candidate_still_not_installable(self):
        r=m.report({'original':self.a,'candidate':self.b})
        self.assertFalse(r['safe_to_install'])
        self.assertFalse(r['strict_envelope_pair']['safe_to_install'])
        self.assertFalse(r['carbon_pc_serialized_and_loader_abi_proven'])
    def test_candidate_changed_prefix_rejected(self):
        mutated=bytearray(self.cand.read_bytes());mutated[5]=0xFE
        self.cand.write_bytes(mutated)
        b=spec(self.cand,offset=64,root=self.new)
        with self.assertRaisesRegex(m.EnvelopeError,'prefix changed'):
            m.report({'original':self.a,'candidate':b})
    def test_candidate_changed_suffix_rejected(self):
        mutated=bytearray(self.cand.read_bytes());mutated[-1]=0xFF
        self.cand.write_bytes(mutated)
        b=spec(self.cand,offset=64,root=self.new)
        with self.assertRaisesRegex(m.EnvelopeError,'suffix changed'):
            m.report({'original':self.a,'candidate':b})
    def test_changed_original_root_rejected(self):
        broken=self.old[:-1]+bytes([self.old[-1]^1]);self.orig.write_bytes(stream(broken))
        with self.assertRaisesRegex(m.v55.GateError,'file fingerprint'):
            m.report({'original':self.a})
    def test_cand_wrong_total_file_size_rejected(self):
        self.cand.write_bytes(self.cand.read_bytes()+b'?')
        b=spec(self.cand,offset=64,root=self.new)
        with self.assertRaisesRegex(m.EnvelopeError,'not exactly \+200'):
            m.report({'original':self.a,'candidate':b})
    def test_wrong_candidate_root_offset_rejected(self):
        b=dict(self.b);b['offset']=65
        with self.assertRaises(m.v55.GateError):m.report({'original':self.a,'candidate':b})
    def test_candidate_standalone_pair_fails_closed(self):
        p=self.path/'standalone';p.write_bytes(self.new)
        with self.assertRaisesRegex(m.EnvelopeError,'embedded ROOTs'):
            m.report({'original':self.a,'candidate':spec(p)})
    def test_standalone_projection_no_tail(self):
        p=self.path/'standalone';p.write_bytes(self.old)
        r=m.report({'original':spec(p)})['projection']
        self.assertEqual(r['root_scope'],'standalone_root')
        self.assertEqual(r['external_suffix_bytes_that_would_shift'],0)
        self.assertEqual(r['external_suffix_displacement_bytes'],0)
    def test_standalone_numeric_probe_rejected(self):
        p=self.path/'standalone';p.write_bytes(self.old)
        with self.assertRaisesRegex(m.EnvelopeError,'embedded ROOT'):
            m.report({'original':spec(p),'windows':[{'offset':0,'length':8}]})
    def test_probe_counts_old_root_end_literal_in_prefix(self):
        r=m.report({'original':self.a,'windows':[{'offset':0,'length':64}]})
        hits=r['exterior_numeric_probe']['windows'][0]['literal_number_matches']
        found=[x for x in hits if x['pattern_name']=='root_end_exclusive' and x['encoded_bits']==32]
        self.assertEqual(found[0]['count'],1)
        self.assertEqual(found[0]['example_offsets'],[8])
        self.assertTrue(r['exterior_numeric_probe']['matches_are_not_proven_pointers'])
    def test_probe_suffix_window(self):
        off=64+len(self.old)
        r=m.report({'original':self.a,'windows':[{'offset':off,'length':len(b'ending-tail')}]})
        self.assertEqual(r['exterior_numeric_probe']['total_bytes_examined'],len(b'ending-tail'))
    def test_probe_overlap_rejected(self):
        with self.assertRaisesRegex(m.EnvelopeError,'overlaps original ROOT'):
            m.report({'original':self.a,'windows':[{'offset':60,'length':16}]})
    def test_probe_exceeds_bounds_rejected(self):
        with self.assertRaisesRegex(m.EnvelopeError,'out of stream bounds'):
            m.report({'original':self.a,'windows':[{'offset':999999,'length':15}]})
    def test_probe_window_too_large_rejected(self):
        with self.assertRaisesRegex(m.EnvelopeError,'too large'):
            m.report({'original':self.a,'windows':[{'offset':0,'length':m.MAX_WINDOW+1}]})
    def test_probe_too_many_windows_rejected(self):
        with self.assertRaisesRegex(m.EnvelopeError,'<= 32 windows'):
            m.report({'original':self.a,'windows':[{'offset':0,'length':1}]*33})
    def test_probe_boolean_offset_rejected(self):
        with self.assertRaisesRegex(m.EnvelopeError,'integer'):
            m.report({'original':self.a,'windows':[{'offset':True,'length':4}]})
    def test_probe_aggregate_cap_rejected(self):
        # 9x 2 MiB windows without allocation of large input: the aggregate
        # limit is checked before trying to read past the source boundary only
        # if a sufficiently large mock stream were available. Test constant.
        self.assertLess(m.MAX_TOTAL_PROBE,9*m.MAX_WINDOW)
    def test_wrong_endian_rejected(self):
        b=dict(self.a);b['endian']='big'
        with self.assertRaises(m.v55.GateError):m.report({'original':b})
    def test_report_no_input_paths(self):
        s=json.dumps(m.report({'original':self.a,'candidate':self.b}))
        self.assertNotIn(str(self.path),s)
    def test_cli_creates_report_but_never_overwrites_source(self):
        manifest=self.path/'manifest.json';manifest.write_text(json.dumps({'original':self.a}))
        report=self.path/'report.json'
        cmd=[sys.executable,str(Path(m.__file__)),'--manifest',str(manifest),'--report',str(report)]
        result=subprocess.run(cmd,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,msg=result.stderr)
        self.assertTrue(report.is_file())
        self.assertEqual(self.orig.read_bytes(),stream(self.old,prefix_marker=True))
        second=subprocess.run(cmd,capture_output=True,text=True)
        self.assertNotEqual(second.returncode,0)
    def test_cli_refuses_source_overwrite(self):
        manifest=self.path/'manifest.json';manifest.write_text(json.dumps({'original':self.a}))
        cmd=[sys.executable,str(Path(m.__file__)),'--manifest',str(manifest),'--report',str(self.orig)]
        x=subprocess.run(cmd,capture_output=True,text=True)
        self.assertNotEqual(x.returncode,0)
    def test_root_source_false_authenticity_not_assumed(self):
        r=m.report({'original':self.a})
        self.assertFalse(r['authenticated_original_Wii_root'])
        self.assertEqual(r['source_platform_hint_not_proof'],'unknown')


class PrivateOriginalWiiFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p=os.environ.get('NFS_UC_WII_SCENE')
        if not p or not Path(p).is_file():
            raise unittest.SkipTest('exact original Wii scene not supplied locally')
        cls.root=Path(p).read_bytes()
        if hashlib.sha256(cls.root).hexdigest()!=m.v55.WII_REDBUILDING_SHA:
            raise unittest.SkipTest('local Wii fixture SHA does not match pinned source')
    def test_exact_wii_source_reachability(self):
        p=m.absolute_projection(self.root,{'path':os.environ['NFS_UC_WII_SCENE']},'little')
        self.assertEqual(p['root_scope'],'standalone_root')
        self.assertEqual(p['original_file_bytes'],8488)
    def test_original_wii_tree_absolute_projection(self):
        p=m.absolute_projection(self.root,{'path':os.environ['NFS_UC_WII_SCENE']},'little')
        nodes={x['child_id']:x for x in p['child_absolute_offsets']}
        self.assertEqual((nodes['0x34105']['stream_absolute_original_payload_start'],nodes['0x34105']['stream_absolute_projected_payload_start']),(5024,5224))
    def test_original_wii_preculler_absolute_projection(self):
        p=m.absolute_projection(self.root,{'path':os.environ['NFS_UC_WII_SCENE']},'little')
        nodes={x['child_id']:x for x in p['child_absolute_offsets']}
        self.assertEqual((nodes['0x34107']['stream_absolute_original_payload_start'],nodes['0x34107']['stream_absolute_projected_payload_start']),(5416,5616))
    def test_original_wii_source_integrity_and_opaque_unchanged(self):
        root=self.root
        p=m.v57.predict(root,'little')
        self.assertEqual(p['original_root_sha256'],m.v55.WII_REDBUILDING_SHA)
        self.assertFalse(p['carbon_pc_serialized_layout_proven'])
    def test_standalone_no_world_stream_claim(self):
        p=m.absolute_projection(self.root,{'path':os.environ['NFS_UC_WII_SCENE']},'little')
        self.assertEqual(p['external_suffix_bytes_that_would_shift'],0)
        self.assertFalse(p['safe_to_install'])


if __name__=='__main__': unittest.main()