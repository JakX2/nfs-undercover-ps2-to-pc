"""V46 fixture-backed structural evidence and negative safety tests."""
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

from v43_spatial_audit import (ROOT, TREE, INST, UNKNOWN, AUX, SOURCE_SHA, AuditError,
                               parse_root, parse_instances)
from v46_evidence_gate import (audit_34107_cadence,inventory_and_gate,MARKER)

DIR=Path(__file__).resolve().parent
WII=DIR/'fixtures'/'UC_Wii_RedBuilding_Original_Scene.chunk'
ORIGINAL=WII.read_bytes()
PARTS=parse_root(ORIGINAL)
OPAQUE=PARTS[UNKNOWN]['data']
EXPECTED_OPAQUE_HASH='438eaa867c378de0d381e4815f45ee453395ab458cf73eb1dcc3985d05992e0b'

class V46VerifiedFixture(unittest.TestCase):
    def test_fixture_integrity(self):self.assertEqual(hashlib.sha256(ORIGINAL).hexdigest(),SOURCE_SHA)
    def test_opaque_integrity(self):self.assertEqual(hashlib.sha256(OPAQUE).hexdigest(),EXPECTED_OPAQUE_HASH)
    def test_wii_identity_is_not_pc(self):
        r=inventory_and_gate(ORIGINAL)
        self.assertEqual(r['source_identity'],'exact-original-UC-Wii-RedBuilding-fixture')
        self.assertFalse(r['original_carbon_pc_provenance_verified'])
        self.assertFalse(r['native_pc_34105_schema_verified'])
        self.assertFalse(r['native_pc_34107_schema_verified'])
    def test_caller_guard_true(self):self.assertTrue(inventory_and_gate(ORIGINAL,expected_sha256=SOURCE_SHA)['caller_supplied_sha256_guard_passed'])
    def test_caller_guard_wrong_refused(self):
        with self.assertRaises(AuditError):inventory_and_gate(ORIGINAL,expected_sha256='0'*64)
    def test_wii_tree_exact(self):self.assertTrue(inventory_and_gate(ORIGINAL)['wii_fixture_48byte_tree_exactly_verified'])
    def test_wii_tree_nodes(self):self.assertEqual(inventory_and_gate(ORIGINAL)['wii_fixture_tree_nodes'],8)
    def test_wii_instances(self):self.assertEqual(inventory_and_gate(ORIGINAL)['candidate_96byte_instance_count'],31)
    def test_wii_aux_per_instance(self):self.assertTrue(inventory_and_gate(ORIGINAL)['aux_32B_per_candidate_instance'])
    def test_wii_opacity_size_hypotheses_both(self):
        r=inventory_and_gate(ORIGINAL)
        self.assertTrue(r['34107_size_equals_96_times_candidate_instance_count_plus_one'])
        self.assertTrue(r['34107_size_equals_384_times_candidate_48byte_nodes'])
    def test_wii_opaque_footer_equals_tree_payload_size(self):
        r=inventory_and_gate(ORIGINAL)
        self.assertEqual(r['tree_34105_bytes'],384)
        self.assertTrue(r['34107_all_populated_footer_words_equal_34105_payload_bytes'])
        self.assertTrue(r['34107_footer_tree_size_correlation_is_not_pointer_proof'])
    def test_wii_no_writer(self):self.assertFalse(inventory_and_gate(ORIGINAL)['game_mod_ready'])
    def test_wii_tree_strides_candidates_only(self):
        r=inventory_and_gate(ORIGINAL)
        self.assertIn(48,r['candidate_divisible_node_strides_bytes'])
        self.assertNotIn(36,r['candidate_divisible_node_strides_bytes'])
    def test_wii_chunk_inventory(self):self.assertEqual(len(inventory_and_gate(ORIGINAL)['chunk_inventory']),6)

class V46Cadence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.r=audit_34107_cadence(OPAQUE)
    def test_opaque_bytes(self):self.assertEqual(self.r['bytes'],3072)
    def test_128_blocks(self):self.assertEqual(self.r['candidate_128_byte_blocks'],24)
    def test_zero_first(self):self.assertEqual(self.r['zero_block_indices'],[0])
    def test_populated_count(self):self.assertEqual(self.r['populated_block_count'],23)
    def test_populated_span(self):self.assertEqual(self.r['populated_block_indices'],list(range(1,24)))
    def test_footer_alignment(self):self.assertEqual(self.r['aligned_384_384_footer_occurrences'],23)
    def test_global_markers(self):self.assertEqual(self.r['u32_pair_384_384_all_occurrences'],25)
    def test_two_offgrid_markers(self):self.assertEqual(self.r['offgrid_384_384_occurrences'],2)
    def test_offgrid_offsets(self):
        self.assertEqual(set(self.r['u32_pair_384_384_offsets'])-set(i*128+120 for i in range(1,24)),{437,2741})
    def test_footer_pair_23(self):self.assertEqual(self.r['populated_128_byte_footer_pairs_histogram'],[{'value':[384,384],'count':23}])
    def test_low_byte_zero(self):self.assertTrue(self.r['all_populated_17_leading_u32_are_multiples_of_256'])
    def test_low_byte_count(self):self.assertEqual(self.r['leading_u32_tested'],391)
    def test_zero_trailing_window(self):self.assertTrue(self.r['all_populated_bytes_67_through_119_zero'])
    def test_distinct_heads(self):self.assertTrue(self.r['populated_first_68_bytes_distinct'])
    def test_semantic_unknown(self):self.assertFalse(self.r['semantic_0x34107_record_decode_proven'])
    def test_no_spurious_head_marker(self):self.assertNotIn(120,self.r['u32_pair_384_384_offsets'])

class V46NegativeEvidence(unittest.TestCase):
    def test_empty_not_claimed_128(self):self.assertFalse(audit_34107_cadence(b'')['candidate_128_byte_aligned'])
    def test_truncated_not_claimed_128(self):self.assertIsNone(audit_34107_cadence(OPAQUE[:-1])['candidate_128_byte_blocks'])
    def test_one_128_block(self):self.assertEqual(audit_34107_cadence(bytes(128))['candidate_128_byte_blocks'],1)
    def test_footer_mutation_decreases_hits(self):
        x=bytearray(OPAQUE);x[248]=0
        self.assertEqual(audit_34107_cadence(x)['aligned_384_384_footer_occurrences'],22)
    def test_leading_low_byte_mutation_flagged(self):
        x=bytearray(OPAQUE);x[128]=1
        self.assertFalse(audit_34107_cadence(x)['all_populated_17_leading_u32_are_multiples_of_256'])
    def test_zero_lane_mutation_flagged(self):
        x=bytearray(OPAQUE);x[128+80]=1
        self.assertFalse(audit_34107_cadence(x)['all_populated_bytes_67_through_119_zero'])
    def test_footer_0x180_is_not_runtime_proof(self):self.assertFalse(audit_34107_cadence(bytes(120)+MARKER)['semantic_0x34107_record_decode_proven'])
    def test_incorrect_root_rejected(self):
        with self.assertRaises(AuditError):inventory_and_gate(b'12345678')
    def test_truncated_child_rejected(self):
        with self.assertRaises(AuditError):inventory_and_gate(ORIGINAL[:-1])
    def test_mutated_source_not_autoclassed_wii(self):
        m=bytearray(ORIGINAL);m[-20]^=1
        r=inventory_and_gate(bytes(m));self.assertEqual(r['source_identity'],'unknown-provenance-root')
        self.assertFalse(r.get('wii_fixture_48byte_tree_exactly_verified',False))
    def test_mutated_source_guard_rejected(self):
        m=bytearray(ORIGINAL);m[-20]^=1
        with self.assertRaises(AuditError):inventory_and_gate(bytes(m),expected_sha256=SOURCE_SHA)
    def test_opaque_without_tree_not_claimed(self):
        # synthetic root cannot gain PC provenance by matching byte shapes
        ch=struct.pack('<II',UNKNOWN,len(OPAQUE))+OPAQUE
        root=struct.pack('<II',ROOT,len(ch))+ch
        r=inventory_and_gate(root)
        self.assertEqual(r['source_identity'],'unknown-provenance-root')
        self.assertFalse(r['native_pc_34107_schema_verified'])
        self.assertNotIn('wii_fixture_48byte_tree_exactly_verified',r)
    def test_source_input_remains_byte_identical(self):
        digest=hashlib.sha256(WII.read_bytes()).hexdigest()
        inventory_and_gate(ORIGINAL)
        self.assertEqual(hashlib.sha256(WII.read_bytes()).hexdigest(),digest)

class V46CommandLine(unittest.TestCase):
    def invoke(self,*args):
        return subprocess.run([sys.executable,str(DIR/'v46_evidence_gate.py'),*map(str,args)],capture_output=True,text=True,cwd=DIR)
    def test_cli_wii_report_with_guard(self):
        with tempfile.TemporaryDirectory() as td:
            target=Path(td)/'report.json'
            cp=self.invoke('--root',WII,'--expected-root-sha256',SOURCE_SHA,'--json',target)
            self.assertEqual(cp.returncode,0,cp.stderr)
            self.assertTrue(json.loads(target.read_text())['root']['wii_fixture_48byte_tree_exactly_verified'])
    def test_cli_bad_sha_no_report(self):
        with tempfile.TemporaryDirectory() as td:
            target=Path(td)/'report.json'
            cp=self.invoke('--root',WII,'--expected-root-sha256','0'*64,'--json',target)
            self.assertNotEqual(cp.returncode,0);self.assertFalse(target.exists())
    def test_cli_cannot_overwrite_source(self):
        cp=self.invoke('--root',WII,'--json',WII)
        self.assertNotEqual(cp.returncode,0)
    def test_cli_cannot_overwrite_report(self):
        with tempfile.TemporaryDirectory() as td:
            target=Path(td)/'report.json';target.write_text('sentinel')
            cp=self.invoke('--root',WII,'--json',target)
            self.assertNotEqual(cp.returncode,0);self.assertEqual(target.read_text(),'sentinel')
    def test_cli_requires_stream_offset(self):
        with tempfile.TemporaryDirectory() as td:
            cp=self.invoke('--stream',WII,'--json',Path(td)/'x.json')
            self.assertNotEqual(cp.returncode,0)
    def test_cli_requires_candidate_for_wii_fixture(self):
        with tempfile.TemporaryDirectory() as td:
            cp=self.invoke('--root',WII,'--wii-fixture',WII,'--json',Path(td)/'x.json')
            self.assertNotEqual(cp.returncode,0)
    def test_cli_stream_offset_0(self):
        with tempfile.TemporaryDirectory() as td:
            target=Path(td)/'report.json'
            cp=self.invoke('--stream',WII,'--offset','0','--json',target)
            self.assertEqual(cp.returncode,0,cp.stderr)
            self.assertEqual(json.loads(target.read_text())['root']['root_size'],8488)
    def test_cli_bad_offset_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            cp=self.invoke('--stream',WII,'--offset','0x1234','--json',Path(td)/'x.json')
            self.assertNotEqual(cp.returncode,0)
    def test_cli_read_only(self):
        with tempfile.TemporaryDirectory() as td:
            before=hashlib.sha256(WII.read_bytes()).hexdigest()
            cp=self.invoke('--root',WII,'--json',Path(td)/'x.json')
            self.assertEqual(cp.returncode,0,cp.stderr)
            self.assertEqual(hashlib.sha256(WII.read_bytes()).hexdigest(),before)

if __name__=='__main__':unittest.main()
