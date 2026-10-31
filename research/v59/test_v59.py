"""V59 asset-free master-table hypothesis tests and optional Wii source fixture.
No original game content is included in this module or GitHub.
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
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'v58'))
import v59_master_index_impact_gate as m
from test_v58 import synthetic_root, appended_root

def sha(b):return hashlib.sha256(b).hexdigest()

def make_master(offsets,stride=92,off_field=20,order='little',chunk_pos=32):
    e='<' if order=='little' else '>'
    rows=bytearray(stride*len(offsets))
    for i,v in enumerate(offsets):
        struct.pack_into(e+'I',rows,i*stride+off_field,v)
    return b'Z'*chunk_pos+struct.pack(e+'II',m.TABLE,len(rows))+rows+b'final'

class V59Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.p=Path(self.tmp.name)
        self.root=synthetic_root()
        self.candidate=appended_root(self.root)
        self.start=128;self.end=self.start+len(self.root)
        self.stream=b'P'*self.start+self.root+b'S'*23
        self.cstream=b'P'*self.start+self.candidate+b'S'*23
        self.master=make_master([16,self.start,self.end,self.end+8])
        self.cmaster=make_master([16,self.start,self.end+200,self.end+208])
        for name,value in [('stream.bin',self.stream),('candidate.bin',self.cstream),('master.bin',self.master),('candidate_master.bin',self.cmaster)]:
            (self.p/name).write_bytes(value)
    def root_spec(self,name,root):
        b=(self.p/name).read_bytes()
        return {'path':str(self.p/name),'label':name,'endian':'little','offset':self.start,
                'expected_file_sha256':sha(b),'expected_root_sha256':sha(root),
                'platform_hint':'unknown'}
    def master_spec(self,name,stride=92,row_count=4,field=20,at=32,base=0):
        b=(self.p/name).read_bytes()
        return {'path':str(self.p/name),'expected_file_sha256':sha(b),
                'chunk_header_offset':at,'row_stride':stride,'row_count':row_count,
                'offset_field':field,'offset_base':base,'endian':'little'}
    def manifest(self,paired=False):
        out={'original_stream':self.root_spec('stream.bin',self.root),
             'original_master':self.master_spec('master.bin'),'target_row':1}
        if paired:
            out['candidate_stream']=self.root_spec('candidate.bin',self.candidate)
            out['candidate_master']=self.master_spec('candidate_master.bin')
        return out
    def test_row_count_and_start(self):
        r=m.report(self.manifest())
        self.assertEqual(r['row_layout']['row_count'],4)
        self.assertEqual(r['root_start'],128)
        self.assertTrue(r['target_offset_matches_pinned_root'])
    def test_root_target_row_unique_when_only_one(self):
        r=m.report(self.manifest());self.assertTrue(r['target_row_mapping_is_unique_under_hypothesis'])
    def test_multiple_identical_root_start_rows_flagged(self):
        (self.p/'master.bin').write_bytes(make_master([self.start,self.start,self.end,self.end+8]))
        r=m.report(self.manifest())
        self.assertFalse(r['target_row_mapping_is_unique_under_hypothesis'])
        self.assertEqual(r['rows_with_candidate_offset_equal_to_root_start'],[0,1])
    def test_predicted_offset_u32_overflow_is_flagged(self):
        fake={'row_stride':92,'offset_field':20,'offset_base':0,'values':[0xFFFFFFFD],
              'rows':b'\0'*92}
        r=m.audit_rows(fake,256,512)
        self.assertEqual(r['candidate_rows'][0]['predicted_offset_if_flat_plus_200'],0xFFFFFFFD+200)
        self.assertFalse(r['candidate_rows'][0]['prediction_fits_declared_u32_field'])
    def test_before_root_unchanged(self):
        r=m.report(self.manifest());self.assertEqual(r['rows']['candidate_rows'][0]['address_relation'],'before_root_unchanged')
    def test_root_start_unchanged(self):
        r=m.report(self.manifest());self.assertEqual(r['rows']['candidate_rows'][1]['predicted_offset_if_flat_plus_200'],128)
    def test_at_root_end_plus_200(self):
        r=m.report(self.manifest());self.assertEqual(r['rows']['candidate_rows'][2]['predicted_offset_if_flat_plus_200'],self.end+200)
    def test_after_root_end_plus_200(self):
        r=m.report(self.manifest());self.assertEqual(r['rows']['candidate_rows'][3]['predicted_offset_if_flat_plus_200'],self.end+208)
    def test_paired_candidate_all_match(self):
        r=m.report(self.manifest(paired=True));self.assertTrue(r['candidate_stream_and_master_passed_narrow_byte_contract'])
        self.assertTrue(all(x['candidate_matches_flat_insertion_projection'] is True for x in r['rows']['candidate_rows']))
    def test_paired_stale_offset_flagged_not_rejected(self):
        (self.p/'candidate_master.bin').write_bytes(self.master)
        r=m.report(self.manifest(paired=True));self.assertFalse(r['rows']['candidate_rows'][2]['candidate_matches_flat_insertion_projection'])
    def test_changed_non_offset_field_flagged(self):
        b=bytearray(self.cmaster);b[32+8+7]=1
        (self.p/'candidate_master.bin').write_bytes(b)
        r=m.report(self.manifest(paired=True))
        self.assertEqual(r['rows']['candidate_rows'][0]['non_offset_field_changed_byte_count'],1)
    def test_inside_root_requires_mapping(self):
        self.master=make_master([16,self.start,self.start+24,self.end])
        (self.p/'master.bin').write_bytes(self.master)
        r=m.report(self.manifest());self.assertIsNone(r['rows']['candidate_rows'][2]['predicted_offset_if_flat_plus_200'])
    def test_wrong_target_offset_rejected(self):
        a=self.manifest();a['target_row']=0
        with self.assertRaisesRegex(m.IndexErrorV59,'does not point'):m.report(a)
    def test_malformed_table_chunk_header_rejected(self):
        (self.p/'master.bin').write_bytes(self.master[:32]+b'BAD!'+self.master[36:])
        with self.assertRaisesRegex(m.IndexErrorV59,'not 0x34110'):m.report(self.manifest())
    def test_wrong_table_declared_size_rejected(self):
        x=bytearray(self.master);struct.pack_into('<I',x,36,4)
        (self.p/'master.bin').write_bytes(x)
        with self.assertRaisesRegex(m.IndexErrorV59,'length does not match'):m.report(self.manifest())
    def test_unknown_master_row_stride_rejected(self):
        a=self.manifest();a['original_master']['row_stride']=91
        with self.assertRaisesRegex(m.IndexErrorV59,'length does not match'):m.report(a)
    def test_field_outside_row_rejected(self):
        a=self.manifest();a['original_master']['offset_field']=90
        with self.assertRaisesRegex(m.IndexErrorV59,'allowed integer range'):m.report(a)
    def test_sha_guard_master(self):
        a=self.manifest();a['original_master']['expected_file_sha256']='0'*64
        with self.assertRaisesRegex(m.IndexErrorV59,'SHA256 mismatch'):m.report(a)
    def test_sha_guard_stream(self):
        a=self.manifest();a['original_stream']['expected_file_sha256']='1'*64
        with self.assertRaisesRegex(m.v55.GateError,'fingerprint'):m.report(a)
    def test_sha_guard_root(self):
        a=self.manifest();a['original_stream']['expected_root_sha256']='2'*64
        with self.assertRaisesRegex(m.v55.GateError,'fingerprint'):m.report(a)
    def test_missing_target_row_fails(self):
        a=self.manifest();del a['target_row']
        with self.assertRaisesRegex(m.IndexErrorV59,'target_row'):m.report(a)
    def test_candidate_stream_alone_rejected(self):
        a=self.manifest();a['candidate_stream']=self.root_spec('candidate.bin',self.candidate)
        with self.assertRaisesRegex(m.IndexErrorV59,'BOTH'):m.report(a)
    def test_candidate_master_alone_rejected(self):
        a=self.manifest();a['candidate_master']=self.master_spec('candidate_master.bin')
        with self.assertRaisesRegex(m.IndexErrorV59,'BOTH'):m.report(a)
    def test_different_candidate_stride_rejected(self):
        a=self.manifest(paired=True);a['candidate_master']['offset_field']=19
        with self.assertRaisesRegex(m.IndexErrorV59,'candidate master offset_field differs'):m.report(a)
    def test_candidate_external_stream_changed_rejected(self):
        c=bytearray(self.cstream);c[-1]=88;(self.p/'candidate.bin').write_bytes(c)
        with self.assertRaisesRegex(m.v58.EnvelopeError,'suffix changed'):m.report(self.manifest(paired=True))
    def test_candidate_external_prefix_changed_rejected(self):
        c=bytearray(self.cstream);c[4]=88;(self.p/'candidate.bin').write_bytes(c)
        with self.assertRaisesRegex(m.v58.EnvelopeError,'prefix changed'):m.report(self.manifest(paired=True))
    def test_unknown_semantics_status(self):
        r=m.report(self.manifest(paired=True))
        self.assertFalse(r['world_index_field_semantics_proven'])
        self.assertFalse(r['carbon_PC_runtime_verified'])
        self.assertFalse(r['safe_to_install'])
    def test_no_user_paths_in_report(self):
        r=m.report(self.manifest(paired=True));self.assertNotIn(str(self.p),json.dumps(r))
    def test_offset_base_explicit(self):
        (self.p/'master.bin').write_bytes(make_master([8,self.start-8,self.end-8,self.end],stride=92))
        a=self.manifest();a['original_master']['offset_base']=8
        r=m.report(a);self.assertEqual(r['root_start'],r['rows']['candidate_rows'][1]['candidate_stream_offset'])
    def test_endian_wrong_rejected(self):
        a=self.manifest();a['original_master']['endian']='big'
        with self.assertRaises(m.IndexErrorV59):m.report(a)
    def test_duplicate_root_not_PC_proof(self):
        r=m.report(self.manifest());self.assertEqual(r['row_layout_evidence_level'],'user_supplied_hypothesis_not_authenticated_Carbon_PC')
    def test_source_stream_required(self):
        with self.assertRaisesRegex(m.IndexErrorV59,'required'):m.report({'original_master':self.master_spec('master.bin')})
    def test_root_embedded_offset_required(self):
        a=self.manifest();del a['original_stream']['offset']
        with self.assertRaisesRegex(m.IndexErrorV59,'embedded root offset'):m.report(a)
    def test_cli_writes_new_report_once(self):
        a=self.manifest();manifest=self.p/'manifest.json';manifest.write_text(json.dumps(a))
        target=self.p/'out.json'
        cmd=[sys.executable,m.__file__,'--manifest',str(manifest),'--report',str(target)]
        r=subprocess.run(cmd,capture_output=True,text=True)
        self.assertEqual(r.returncode,0,msg=r.stderr)
        self.assertFalse(json.loads(target.read_text())['safe_to_install'])
        r=subprocess.run(cmd,capture_output=True,text=True)
        self.assertNotEqual(r.returncode,0)
    def test_cli_refuses_source_overwrite(self):
        a=self.manifest();manifest=self.p/'manifest.json';manifest.write_text(json.dumps(a))
        cmd=[sys.executable,m.__file__,'--manifest',str(manifest),'--report',str(self.p/'stream.bin')]
        r=subprocess.run(cmd,capture_output=True,text=True)
        self.assertNotEqual(r.returncode,0)

class PinnedWiiWithSyntheticMasterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p=os.environ.get('NFS_UC_WII_SCENE')
        if not p or not Path(p).is_file():raise unittest.SkipTest('private original Wii ROOT absent')
        cls.root=Path(p).read_bytes()
        if sha(cls.root)!=m.v55.WII_REDBUILDING_SHA:raise AssertionError('original Wii source SHA mismatch')
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.p=Path(self.tmp.name)
        self.start=256
        self.stream=b'Z'*self.start+self.root+b'SUFFIX'
        self.master=make_master([24,self.start,self.start+len(self.root)],chunk_pos=24)
        (self.p/'stream.bin').write_bytes(self.stream)
        (self.p/'master.bin').write_bytes(self.master)
        self.m={'original_stream':{'path':str(self.p/'stream.bin'),'label':'real-Wii-root-in-synthetic-wrapper',
             'expected_file_sha256':sha(self.stream),'expected_root_sha256':sha(self.root),'endian':'little','offset':self.start},
            'original_master':{'path':str(self.p/'master.bin'),'expected_file_sha256':sha(self.master),
             'chunk_header_offset':24,'row_count':3,'row_stride':92,'offset_field':20,'endian':'little'},
            'target_row':1}
    def test_source_hash_guard_and_index_row(self):
        r=m.report(self.m)
        self.assertEqual(r['source_root_sha256'],m.v55.WII_REDBUILDING_SHA)
        self.assertTrue(r['target_offset_matches_pinned_root'])
    def test_root_end_projection(self):
        r=m.report(self.m); self.assertEqual(r['rows']['candidate_rows'][2]['predicted_offset_if_flat_plus_200'],self.start+len(self.root)+200)
    def test_source_not_mistaken_for_original_carbon_master(self):
        r=m.report(self.m);self.assertEqual(r['row_layout_evidence_level'],'user_supplied_hypothesis_not_authenticated_Carbon_PC')
        self.assertFalse(r['world_index_field_semantics_proven'])

if __name__=='__main__':unittest.main()