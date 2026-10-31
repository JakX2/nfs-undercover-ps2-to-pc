"""V57 source-only append-address-shift regression tests.

Optional exact original Wii scene supplied via NFS_UC_WII_SCENE; all synthetic
roots are generated in memory and no proprietary data is committed.
"""
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
import v57_append_layout_gate as m

SCENE=m.v55.SCENE
TREE=m.v55.TREE
PREC=m.v55.PRECULL
INFO=m.INFO
INST=m.INST
AUX=m.AUX


def frame(chunks, order='little'):
    e=m.v55.endian(order)
    b=b''.join(struct.pack(e+'II',tag,len(content))+content for tag,content in chunks)
    return struct.pack(e+'II',m.v55.ROOT,len(b))+b


def synthetic(info_first=True, scene_len=68, order='little', pairs=1):
    e=m.v55.endian(order)
    layout=[(SCENE,bytes(scene_len)),(INFO,bytes(72)),(INST,bytes(96*pairs)),
            (AUX,bytes(32*pairs)),(TREE,bytes(48)),(PREC,bytes(128))]
    if not info_first:
        layout[1],layout[2]=layout[2],layout[1]
    # Calculate only alignment prefix length in the instance table.
    pos=8;built=[]
    for tag,b in layout:
        start=pos+8
        if tag==INST:
            b=b'\x11'*((-start)&15)+b
        built.append((tag,b));pos=start+len(b)
    return frame(built,order)


def appended(root,order='little'):
    e=m.v55.endian(order)
    ch=m.v55.children(root,order)
    return frame([(tag,b+bytes(m.EXPECTED_APPEND.get(tag,0))) for tag,(start,b) in ch.items()],order)


def spec(path,order='little'):
    b=path.read_bytes()
    return {'label':'synthetic','path':str(path),'endian':order,
            'expected_file_sha256':m.v55.sha256(b),'expected_root_sha256':m.v55.sha256(b)}


class Synthetic(unittest.TestCase):
    def test_candidate_instance_after_info_has_shift(self):
        r=m.predict(synthetic(True),'little')['candidate_wii_96_row_layout']
        self.assertTrue(r['root_relative_alignment_residue_changes'])
        self.assertFalse(r['unchanged_prefix_plus_96_append_still_shape_compatible'])
        self.assertEqual(r['projected_root_relative_payload_start']-r['original_root_relative_payload_start'],72)
    def test_candidate_instance_before_info_no_shift(self):
        r=m.predict(synthetic(False),'little')['candidate_wii_96_row_layout']
        self.assertFalse(r['root_relative_alignment_residue_changes'])
        self.assertTrue(r['unchanged_prefix_plus_96_append_still_shape_compatible'])
        self.assertEqual(r['projected_root_relative_payload_start']-r['original_root_relative_payload_start'],0)
    def test_projected_size_plus_200(self):
        b=synthetic();r=m.predict(b,'little')
        self.assertEqual(r['projected_root_bytes']-len(b),200)
        self.assertFalse(r['safe_to_install'])
    def test_preceding_child_shifts(self):
        r=m.predict(synthetic(True),'little')
        shifts={x['child_id']:x['offset_shift'] for x in r['projected_children']}
        self.assertEqual(shifts['0x34102'],0)
        self.assertEqual(shifts['0x34103'],72)
        self.assertEqual(shifts['0x3410D'],168)
        self.assertEqual(shifts['0x34105'],200)
        self.assertEqual(shifts['0x34107'],200)
    def test_append_pair_matches_projection(self):
        a=synthetic(True);b=appended(a)
        p=m.audit_pair(a,b,'little')
        self.assertTrue(p['byte_preserving_append_contract_passed'])
        self.assertFalse(p['safe_to_install'])
        self.assertEqual(p['candidate_wii_96_row_layout']['prefix_bytes_change'],8)
    def test_append_pair_before_info_keeps_instance_alignment(self):
        a=synthetic(False);b=appended(a)
        p=m.audit_pair(a,b,'little')
        self.assertTrue(p['candidate_wii_96_row_layout']['unchanged_prefix_plus_96_append_still_shape_compatible'])
    def test_four_initial_alignment_residues(self):
        for n in (68,72,76,80):
            with self.subTest(scene_len=n):
                r=m.predict(synthetic(True,n),'little')['candidate_wii_96_row_layout']
                self.assertIn(r['original_alignment_prefix_bytes'],(0,4,8,12))
                self.assertFalse(r['unchanged_prefix_plus_96_append_still_shape_compatible'])
    def test_big_endian_simulated(self):
        a=synthetic(True,order='big');b=appended(a,'big')
        self.assertTrue(m.audit_pair(a,b,'big')['byte_preserving_append_contract_passed'])
    def test_wrong_endianness_fails(self):
        with self.assertRaises(m.v55.GateError):m.predict(synthetic(True,order='big'),'little')
    def test_malformed_root_rejected(self):
        with self.assertRaises(m.v55.GateError):m.predict(synthetic(True)[:-1],'little')
    def test_missing_info_rejected(self):
        a=synthetic();x=m.v55.children(a,'little')
        bad=frame([(t,v[1]) for t,v in x.items() if t!=INFO])
        with self.assertRaisesRegex(m.LayoutError,'required'):m.predict(bad,'little')
    def test_missing_aux_rejected(self):
        a=synthetic();x=m.v55.children(a,'little')
        bad=frame([(t,v[1]) for t,v in x.items() if t!=AUX])
        with self.assertRaisesRegex(m.LayoutError,'required'):m.predict(bad,'little')
    def test_unmodified_candidate_rejected(self):
        a=synthetic()
        with self.assertRaisesRegex(m.LayoutError,'200'):m.audit_pair(a,a,'little')
    def test_corrupt_existing_child_rejected(self):
        a=synthetic();x=m.v55.children(appended(a),'little')
        bad=frame([(t,(bytes([v[1][0]^1])+v[1][1:]) if t==TREE else v[1]) for t,v in x.items()])
        with self.assertRaisesRegex(m.LayoutError,'not preserved'):m.audit_pair(a,bad,'little')
    def test_wrong_extra_instance_length_rejected(self):
        a=synthetic();x=m.v55.children(appended(a),'little')
        bad=frame([(t,v[1]+b'\0') if t==INST else (t,v[1]) for t,v in x.items()])
        with self.assertRaisesRegex(m.LayoutError,'200'):m.audit_pair(a,bad,'little')
    def test_order_changed_rejected(self):
        a=synthetic();x=list(m.v55.children(appended(a),'little').items())
        x[1],x[2]=x[2],x[1]
        bad=frame([(t,v[1]) for t,v in x])
        with self.assertRaisesRegex(m.LayoutError,'child order'):m.audit_pair(a,bad,'little')
    def test_changed_bytes_in_existing_info_rejected(self):
        a=synthetic();ch=m.v55.children(appended(a),'little')
        bad=frame([(t, (b'\x01'+v[1][1:]) if t==INFO else v[1]) for t,v in ch.items()])
        with self.assertRaisesRegex(m.LayoutError,'original child bytes'):m.audit_pair(a,bad,'little')
    def test_missing_source_fingerprint_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'src';p.write_bytes(synthetic())
            s=spec(p);del s['expected_file_sha256']
            with self.assertRaisesRegex(m.v55.GateError,'missing manifest'):m.report_from_manifest({'original':s})
    def test_source_sha_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'src';p.write_bytes(synthetic())
            s=spec(p);s['expected_root_sha256']='a'*64
            with self.assertRaisesRegex(m.v55.GateError,'fingerprint mismatch'):m.report_from_manifest({'original':s})
    def test_manifest_report_no_paths_or_source_bytes(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'secret-game-file';p.write_bytes(synthetic())
            r=m.report_from_manifest({'original':spec(p)})
            serialized=json.dumps(r)
            self.assertNotIn('secret-game-file',serialized)
            self.assertFalse(r['safe_to_install'])
            self.assertEqual(r['original_source_authentication'],'unknown_provenance')
    def test_verified_pair_manifest(self):
        with tempfile.TemporaryDirectory() as t:
            d=Path(t);p=d/'original';q=d/'candidate';p.write_bytes(synthetic());q.write_bytes(appended(p.read_bytes()))
            r=m.report_from_manifest({'original':spec(p),'candidate':spec(q)})
            self.assertTrue(r['paired_append']['byte_preserving_append_contract_passed'])
            self.assertFalse(r['carbon_pc_abi_proven'])
    def test_candidate_endian_mismatch(self):
        with tempfile.TemporaryDirectory() as t:
            d=Path(t);p=d/'a';q=d/'b';p.write_bytes(synthetic());q.write_bytes(appended(p.read_bytes()))
            with self.assertRaisesRegex(m.v55.GateError,'root header'):m.report_from_manifest({'original':spec(p),'candidate':spec(q,'big')})
    def test_cli_refuses_existing_report(self):
        with tempfile.TemporaryDirectory() as t:
            d=Path(t);p=d/'original';p.write_bytes(synthetic());manifest=d/'manifest.json';manifest.write_text(json.dumps({'original':spec(p)}));report=d/'report';report.write_text('KEEP')
            x=subprocess.run([sys.executable,str(Path(m.__file__)),'--manifest',str(manifest),'--report',str(report)],capture_output=True,text=True)
            self.assertNotEqual(x.returncode,0);self.assertEqual(report.read_text(),'KEEP')
    def test_cli_report_output_and_no_overwrite_of_source(self):
        with tempfile.TemporaryDirectory() as t:
            d=Path(t);p=d/'private-original';b=synthetic();p.write_bytes(b);manifest=d/'manifest.json';manifest.write_text(json.dumps({'original':spec(p)}));report=d/'report.json'
            cmd=[sys.executable,str(Path(m.__file__)),'--manifest',str(manifest),'--report',str(report)]
            x=subprocess.run(cmd,capture_output=True,text=True)
            self.assertEqual(x.returncode,0,msg=x.stderr)
            self.assertTrue(report.exists());self.assertEqual(p.read_bytes(),b)
            self.assertNotIn('private-original',report.read_text())
            y=subprocess.run(cmd,capture_output=True,text=True)
            self.assertNotEqual(y.returncode,0)
    def test_no_unverified_pc_install_claim(self):
        r=m.predict(synthetic(True),'little')
        self.assertFalse(r['carbon_pc_serialized_layout_proven']);self.assertFalse(r['safe_to_install'])
    def test_original_byte_mutation_in_aux_rejected(self):
        a=synthetic(False);ch=m.v55.children(appended(a),'little')
        bad=frame([(t, b'\x7f'+v[1][1:] if t==AUX else v[1]) for t,v in ch.items()])
        with self.assertRaisesRegex(m.LayoutError,'not preserved'):m.audit_pair(a,bad,'little')

class PrivateOriginal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p=os.getenv('NFS_UC_WII_SCENE')
        if not p or not Path(p).is_file():raise unittest.SkipTest('private Wii fixture unavailable')
        cls.raw=Path(p).read_bytes()
        if hashlib.sha256(cls.raw).hexdigest()!=m.v55.WII_REDBUILDING_SHA:
            raise unittest.SkipTest('private Wii fixture SHA differs from pinned original')
        cls.result=m.predict(cls.raw,'little')
    def test_original_offsets(self):
        x={r['child_id']:r for r in self.result['projected_children']}
        self.assertEqual(x['0x34103']['original_payload_start'],92)
        self.assertEqual(x['0x34102']['original_payload_start'],3080)
        self.assertEqual(x['0x34105']['original_payload_start'],5024)
        self.assertEqual(x['0x34107']['original_payload_start'],5416)
    def test_instance_before_info_stays_at_same_start(self):
        p=self.result['candidate_wii_96_row_layout']
        self.assertEqual(p['original_root_relative_payload_start'],92)
        self.assertEqual(p['projected_root_relative_payload_start'],92)
        self.assertTrue(p['unchanged_prefix_plus_96_append_still_shape_compatible'])
    def test_tree_preculler_absolute_offsets_shift(self):
        x={r['child_id']:r for r in self.result['projected_children']}
        self.assertEqual(x['0x34105']['offset_shift'],200)
        self.assertEqual(x['0x34107']['offset_shift'],200)
        self.assertTrue(x['0x34105']['offset_residue16_changes'])
    def test_original_root_projected_lengths(self):
        self.assertEqual(self.result['original_root_bytes'],8488)
        self.assertEqual(self.result['projected_root_bytes'],8688)
    def test_original_is_read_only_and_not_installable(self):
        self.assertFalse(self.result['safe_to_install'])
        self.assertFalse(self.result['carbon_pc_serialized_layout_proven'])

if __name__=='__main__':unittest.main()