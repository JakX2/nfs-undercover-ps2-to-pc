"""V62 strict V61->V60 handoff checks: 100% synthetic except pinned source case."""
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
import v62_ambiguity_safe_anchor_gate as m
WII_SHA='cb08ca728a9b76992aaaefe32b450565ef53246f090cfe296f77d96c5d272e7f'


def sha(b): return hashlib.sha256(b).hexdigest()
def child(id,blob,e='<'):return struct.pack(e+'II',id,len(blob))+blob
def root(num=1,children=None,e='<'):
    if children is None:
        children=[child(m.v61.SCENE,struct.pack(e+'I',num),e),
                  child(m.v61.INSTANCE,b'x'*96,e)]
    d=b''.join(children)
    return struct.pack(e+'II',m.v61.ROOT,len(d))+d

def nested(inner=None):
    inner=root(9) if inner is None else inner
    return root(19,[child(m.v61.SCENE,b'0000'),child(m.v61.INSTANCE,inner)])

class SyntheticV62(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'source.bin'
    def audit(self,blob,**kw):
        self.path.write_bytes(blob)
        return m.audit_file(self.path,sha(blob),'little',**kw)['v62_gate']
    def test_two_disjoint_roots_eligible(self):
        a,b=root(1),root(2)
        x=self.audit(b'P'*17+a+b'Q'*19+b)
        self.assertTrue(x['whole_file_scan_complete'])
        self.assertEqual([z['offset'] for z in x['eligible_v60_anchor_shortlist_unverified']],[17,17+len(a)+19])
        self.assertEqual(x['excluded_ambiguous_candidate_count'],0)
        self.assertEqual(x['candidate_root_count'],2)
    def test_nested_two_scenery_roots_are_both_excluded(self):
        x=self.audit(nested())
        self.assertEqual(x['candidate_root_count'],2)
        self.assertEqual(x['excluded_ambiguous_candidate_count'],2)
        self.assertEqual(x['eligible_count'],0)
        self.assertEqual(len(x['overlap_pair_offsets']),1)
        self.assertEqual(x['raw_v61_shortlist_count'],2)
    def test_nested_plus_independent_preserves_only_independent(self):
        z=root(42);u=nested();x=self.audit(u+b'!'+z)
        self.assertEqual(x['excluded_ambiguous_candidate_count'],2)
        self.assertEqual([y['offset'] for y in x['eligible_v60_anchor_shortlist_unverified']],[len(u)+1])
    def test_nested_other_tlv_candidate_blocks_scenery_child(self):
        # The parent is not a scenery candidate, yet still overlaps the child.
        n=root(13)
        p=root(2,[child(0x777,n)])
        x=self.audit(p)
        self.assertEqual(x['candidate_root_count'],2)
        self.assertEqual(x['raw_v61_shortlist_count'],1)
        self.assertEqual(x['eligible_count'],0)
        self.assertEqual(x['excluded_ambiguous_candidate_count'],2)
    def test_two_nested_children_both_excluded(self):
        a=root(31);b=root(32)
        p=root(1,[child(m.v61.SCENE,b'1111'),child(m.v61.INSTANCE,a+b)])
        x=self.audit(p)
        self.assertEqual(x['candidate_root_count'],3)
        self.assertEqual(x['excluded_ambiguous_candidate_count'],3)
        self.assertEqual(x['eligible_count'],0)
    def test_touching_boundaries_allowed(self):
        a,b=root(1),root(2)
        x=self.audit(a+b)
        self.assertEqual(x['eligible_count'],2)
    def test_repeated_source_bytes_only_one_anchor(self):
        a=root(1);x=self.audit(a+a)
        self.assertEqual(x['candidate_root_count'],2)
        self.assertEqual(x['eligible_count'],1)
        self.assertEqual(x['excluded_same_byte_candidate_offsets'],[len(a)])
    def test_window_start_cannot_prove_disjointness(self):
        a=root(1);x=self.audit(b'P'*3+a,start_offset=3)
        self.assertFalse(x['whole_file_scan_complete'])
        self.assertEqual(x['eligible_count_before_scan_completeness_gate'],1)
        self.assertEqual(x['eligible_count'],0)
    def test_window_end_cannot_prove_disjointness(self):
        a=root(1);x=self.audit(a+b'F'*5,stop_offset=1)
        self.assertEqual(x['candidate_root_count'],1)
        self.assertEqual(x['eligible_count'],0)
    def test_limited_scan_cannot_release_anchors(self):
        a,b=root(1),root(2)
        x=self.audit(a+b,max_candidates=1)
        self.assertEqual(x['candidate_root_count'],1)
        self.assertFalse(x['whole_file_scan_complete'])
        self.assertEqual(x['eligible_count'],0)
    def test_empty_stream(self):
        x=self.audit(b'')
        self.assertTrue(x['whole_file_scan_complete'])
        self.assertEqual(x['eligible_count'],0)
    def test_non_scenery_root_not_eligible(self):
        x=self.audit(root(1,[child(0x777,b'0123')]))
        self.assertEqual(x['eligible_count'],0)
        self.assertEqual(x['candidate_root_count'],1)
    def test_corrupted_root_has_no_anchors(self):
        a=root(1);x=self.audit(a[:-1])
        self.assertEqual(x['eligible_count'],0)
    def test_hash_failure_before_scan(self):
        self.path.write_bytes(root(1))
        with self.assertRaises(m.v61.InventoryError):
            m.audit_file(self.path,'0'*64,'little')
    def test_big_endian(self):
        a=root(12,e='>')
        self.path.write_bytes(a)
        x=m.audit_file(self.path,sha(a),'big')['v62_gate']
        self.assertEqual(x['eligible_count'],1)
    def test_wrong_endian_empty(self):
        a=root(12,e='>')
        x=self.audit(a)
        self.assertEqual(x['eligible_count'],0)
    def test_no_install_or_loader_claims(self):
        x=self.audit(root(1))
        self.assertFalse(x['safe_to_install'])
        self.assertFalse(x['native_carbon_root_ownership_proven'])
        self.assertFalse(x['native_carbon_master_index_or_loader_proven'])
        self.assertTrue(x['source_hash_does_not_prove_original_game_provenance'])
    def test_schema_fail_closed(self):
        x=self.audit(root(1))
        x['schema']='bad'
        with self.assertRaises(m.OwnershipError):m.filter_candidates(x)
    def test_false_readonly_rejected(self):
        self.path.write_bytes(root(1))
        x=m.v61.audit_file(self.path,expected_sha256=sha(root(1)),endian='little')
        x['read_only']=False
        with self.assertRaises(m.OwnershipError):m.filter_candidates(x)
    def test_forged_install_flag_rejected(self):
        self.path.write_bytes(root(1))
        x=m.v61.audit_file(self.path,expected_sha256=sha(root(1)),endian='little')
        x['safe_to_install']=True
        with self.assertRaises(m.OwnershipError):m.filter_candidates(x)
    def test_malformed_interval_rejected(self):
        self.path.write_bytes(root(1));x=m.v61.audit_file(self.path,expected_sha256=sha(root(1)),endian='little')
        x['candidate_roots'][0]['end_exclusive']=True
        with self.assertRaises(m.OwnershipError):m.filter_candidates(x)
    def test_65_distinct_root_shortlist_bounded(self):
        buf=b''.join(root(i) for i in range(65))
        x=self.audit(buf)
        self.assertEqual(x['eligible_count_before_scan_completeness_gate'],65)
        self.assertEqual(x['eligible_count'],64)
        self.assertTrue(x['shortlist_truncated_at_64'])
    def test_hundreds_nested_bounded_report(self):
        inside=b''.join(root(i) for i in range(100))
        outer=root(99,[child(m.v61.SCENE,b'0123'),child(m.v61.INSTANCE,inside)])
        x=self.audit(outer)
        self.assertEqual(x['excluded_ambiguous_candidate_count'],101)
        self.assertEqual(x['eligible_count'],0)
        self.assertLessEqual(len(x['overlap_pair_offsets']),100)
    def test_no_private_paths_in_report(self):
        blob=root(1);self.path.write_bytes(blob)
        rep=json.dumps(m.audit_file(self.path,sha(blob),'little'))
        self.assertNotIn(str(self.path),rep)
        self.assertNotIn(self.path.name,rep)
    def test_cli_output_readonly_and_no_overwrite(self):
        a=root(1);self.path.write_bytes(a)
        cmd=[sys.executable,str(Path(m.__file__)),'--source',str(self.path),
             '--expected-file-sha256',sha(a),'--endian','little','--report',str(self.path.parent/'out.json')]
        p=subprocess.run(cmd,capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr)
        report=json.loads((self.path.parent/'out.json').read_text())
        self.assertEqual(report['v62_gate']['eligible_count'],1)
        self.assertEqual(self.path.read_bytes(),a)
        p=subprocess.run(cmd,capture_output=True,text=True)
        self.assertNotEqual(p.returncode,0)
    def test_cli_rejects_source_as_report(self):
        a=root(1);self.path.write_bytes(a)
        p=subprocess.run([sys.executable,str(Path(m.__file__)),'--source',str(self.path),
              '--expected-file-sha256',sha(a),'--endian','little',
              '--report',str(self.path)],capture_output=True,text=True)
        self.assertNotEqual(p.returncode,0)
        self.assertEqual(self.path.read_bytes(),a)
    def test_v60_handoff_with_two_disjoint_synthetic_roots(self):
        a,b=root(1),root(2);source=b'X'*40+a+b'Y'*22+b
        x=self.audit(source)
        anchors=x['eligible_v60_anchor_shortlist_unverified']
        self.assertEqual(len(anchors),2)
        sys.path.insert(0,str(Path(__file__).resolve().parents[1] / 'v60'))
        import v60_multi_anchor_index_gate as v60
        table=bytearray(3*92)
        struct.pack_into('<I',table,92+20,anchors[0]['offset'])
        struct.pack_into('<I',table,2*92+20,anchors[1]['offset'])
        master=b'H'*16+struct.pack('<II',0x34110,len(table))+table
        mf=self.path.parent/'master.bin';mf.write_bytes(master)
        manifest={'stream':{'path':str(self.path),'expected_file_sha256':sha(source),'endian':'little'},
            'master':{'path':str(mf),'expected_file_sha256':sha(master),'chunk_header_offset':16,'endian':'little'},
            'roots':anchors,
            'hypotheses':[{'id':'synthetic_92_at_20','row_stride':92,'row_count':3,'offset_field':20}]}
        result=v60.evaluate_layouts(manifest)
        self.assertEqual(result['candidate_layouts'][0]['structural_status'],
                         'multiple_distinct_roots_structurally_match_NOT_loader_proof')
        self.assertFalse(result['safe_to_install'])

class PinnedWiiV62(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        src=os.environ.get('NFS_UC_WII_SCENE')
        if not src or not Path(src).is_file():
            raise unittest.SkipTest('private original Wii fixture unavailable')
        cls.blob=Path(src).read_bytes()
        if sha(cls.blob)!=WII_SHA:
            raise unittest.SkipTest('original fixture did not match exact SHA')
    def scan(self,blob):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'private-input';p.write_bytes(blob)
            return m.audit_file(p,sha(blob),'little')['v62_gate']
    def test_genuine_root_candidate_eligible_but_not_proven(self):
        x=self.scan(self.blob)
        self.assertEqual(x['eligible_count'],1)
        self.assertEqual(x['eligible_v60_anchor_shortlist_unverified'][0]['expected_root_sha256'],WII_SHA)
        self.assertFalse(x['native_carbon_root_ownership_proven'])
    def test_two_original_copies_not_independent(self):
        x=self.scan(self.blob*2)
        self.assertEqual(x['candidate_root_count'],2)
        self.assertEqual(x['eligible_count'],1)
        self.assertEqual(x['excluded_same_byte_candidate_offsets'],[8488])
    def test_original_root_nested_is_ambiguous(self):
        blob=nested(self.blob)
        x=self.scan(blob)
        self.assertEqual(x['eligible_count'],0)
        self.assertEqual(x['excluded_ambiguous_candidate_count'],2)
    def test_original_root_adjacent_to_distinct_synthetic(self):
        b=self.blob+root(25)
        x=self.scan(b)
        self.assertEqual(x['eligible_count'],2)
        self.assertEqual(x['eligible_v60_anchor_shortlist_unverified'][0]['expected_root_sha256'],WII_SHA)
    def test_partial_original_scan_never_handoffs(self):
        x=self.scan(self.blob)
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'f';p.write_bytes(self.blob)
            partial=m.audit_file(p,WII_SHA,'little',stop_offset=1)['v62_gate']
        self.assertEqual(x['eligible_count'],1)
        self.assertEqual(partial['eligible_count'],0)

if __name__=='__main__':unittest.main()