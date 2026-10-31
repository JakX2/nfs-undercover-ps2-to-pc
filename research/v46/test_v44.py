"""Source-backed, READ-ONLY V44 tests. All expected 'shape' rules are fixture observations only."""
import collections
import hashlib
import json
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from v43_spatial_audit import SOURCE_SHA, parse_root, UNKNOWN, ROOT, AuditError
from v44_34107_discriminator import audit_root, audit_opaque, census_world

SRC=Path(__file__).parent/'fixtures'/'UC_Wii_RedBuilding_Original_Scene.chunk'
BLOB=SRC.read_bytes()
U=parse_root(BLOB)[UNKNOWN]['data']

class V44Tests(unittest.TestCase):
    def test01_source_file_sha_guard(self):
        self.assertEqual(hashlib.sha256(BLOB).hexdigest(),SOURCE_SHA)
    def test02_root_sha_guard(self):
        self.assertTrue(audit_root(BLOB,expected_sha256=SOURCE_SHA)['source_sha256_guard_checked'])
    def test03_wrong_hash_rejected(self):
        with self.assertRaisesRegex(AuditError,'SHA256'):
            audit_root(BLOB,expected_sha256='a'*64)
    def test04_original_scene_root_size(self):
        self.assertEqual(len(BLOB),8488)
    def test05_34107_size(self):
        self.assertEqual(len(U),3072)
    def test06_128_block_count(self):
        self.assertEqual(audit_root(BLOB)['128_byte_candidate_blocks'],24)
    def test07_one_zero_block(self):
        self.assertEqual(audit_root(BLOB)['128_byte_zero_block_indices'],[0])
    def test08_nonzero_count(self):
        self.assertEqual(sum(b!=0 for b in U),607)
    def test09_exact_footer_values(self):
        r=audit_root(BLOB)
        self.assertEqual(r['populated_block_tail_pair_histogram'],[{'u32_pair':[384,384],'count':23}])
    def test10_header_distribution(self):
        a={x['hex']:x['count'] for x in audit_root(BLOB)['populated_block_header_u32_histogram']}
        self.assertEqual(a,{'0x0007E700':22,'0x0003E700':1})
    def test11_all_23_nonzero_blocks_are_distinct(self):
        rows=audit_root(BLOB)['128_byte_blocks']
        self.assertEqual(len({r['sha256'] for r in rows if not r['all_zero']}),23)
    def test12_three_size_hypotheses(self):
        h=audit_root(BLOB)['size_hypotheses']
        self.assertTrue(h['96_bytes_times_instances_plus_one'])
        self.assertFalse(h['96_bytes_times_instances'])
        self.assertTrue(h['384_bytes_times_48byte_node_count'])
    def test13_opaque_marker_and_no_writer(self):
        r=audit_root(BLOB)
        self.assertFalse(r['safe_native_34107_writer_exists'])
        self.assertFalse(r['loader_scenery_execution_confirmed'])
        self.assertIn('opaque',r['interpretation'])
    def test14_instance_discriminating_hypothesis(self):
        r=audit_opaque(U,31,7)['size_hypotheses']
        self.assertTrue(r['96_bytes_times_instances_plus_one'])
        self.assertFalse(r['384_bytes_times_48byte_node_count'])
    def test15_node_discriminating_hypothesis(self):
        r=audit_opaque(U,30,8)['size_hypotheses']
        self.assertFalse(r['96_bytes_times_instances_plus_one'])
        self.assertTrue(r['384_bytes_times_48byte_node_count'])
    def test16_both_false_candidate(self):
        r=audit_opaque(U,30,7)['size_hypotheses']
        self.assertFalse(r['96_bytes_times_instances_plus_one'])
        self.assertFalse(r['384_bytes_times_48byte_node_count'])
    def test17_mutating_footer_detected_not_silently_normalized(self):
        x=bytearray(U)
        x[128+120]=0xAA
        r=audit_opaque(bytes(x),31,8)
        self.assertLess(r['dominant_tail_pair_share'],1)
        self.assertNotEqual(r['sha256'],hashlib.sha256(U).hexdigest())
    def test18_sub128_payload_no_invented_blocks(self):
        r=audit_opaque(b'\x00'*140,3,None)
        self.assertIsNone(r['128_byte_candidate_blocks'])
        self.assertEqual(r['128_byte_blocks'],[])
    def test19_one_original_root_census(self):
        r=census_world(BLOB)
        self.assertEqual(r['counts']['scene_roots'],1)
        self.assertEqual(r['counts']['both_hypotheses_true'],1)
    def test20_two_original_roots_census(self):
        r=census_world(BLOB*2)
        self.assertEqual(r['counts']['scene_roots'],2)
        self.assertEqual(r['counts']['both_hypotheses_true'],2)
        self.assertEqual(r['examples'][1]['root_offset_hex'],hex(8488))
    def test21_other_top_level_chunk_skipped(self):
        prefix=struct.pack('<II',0x12345678,4)+b'\0'*4
        r=census_world(prefix+BLOB)
        self.assertEqual(r['counts']['top_level_chunks'],2)
        self.assertEqual(r['counts']['scene_roots'],1)
        self.assertEqual(r['examples'][0]['root_offset_hex'],hex(12))
    def test22_invalid_top_level_length_rejected(self):
        with self.assertRaises(AuditError):
            census_world(struct.pack('<II',ROOT,10000)+b'a')
    def test23_max_roots(self):
        r=census_world(BLOB*3,max_roots=1)
        self.assertEqual(r['counts']['scene_roots'],1)
        self.assertEqual(r['bytes_scanned'],len(BLOB))
    def test24_report_does_not_invent_spatial_schema(self):
        r=audit_root(BLOB)
        self.assertIsNone(r.get('semantic_writable_schema'))
        self.assertFalse(r['carbon_pc_schema_verified'])
    def test25_cli_source_protection(self):
        cmd=[sys.executable,str(Path(__file__).parent/'v44_34107_discriminator.py'),'--scene',str(SRC),'--json',str(SRC)]
        completed=subprocess.run(cmd,capture_output=True,text=True)
        self.assertNotEqual(completed.returncode,0)
    def test26_cli_original_verified_output(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'test.json'
            cmd=[sys.executable,str(Path(__file__).parent/'v44_34107_discriminator.py'),'--scene',str(SRC),'--expected-sha256',SOURCE_SHA,'--json',str(p)]
            completed=subprocess.run(cmd,capture_output=True,text=True)
            self.assertEqual(completed.returncode,0,completed.stderr)
            self.assertEqual(json.loads(p.read_text())['source_root_sha256'],SOURCE_SHA)
            self.assertEqual(hashlib.sha256(SRC.read_bytes()).hexdigest(),SOURCE_SHA)
    def test27_cli_refuses_existing_report(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'test.json';p.write_text('preserve')
            cmd=[sys.executable,str(Path(__file__).parent/'v44_34107_discriminator.py'),'--scene',str(SRC),'--json',str(p)]
            completed=subprocess.run(cmd,capture_output=True,text=True)
            self.assertNotEqual(completed.returncode,0)
            self.assertEqual(p.read_text(),'preserve')
    def test28_cli_stream_extracts_exact_root(self):
        with tempfile.TemporaryDirectory() as d:
            prefix=struct.pack('<II',0x12345678,4)+b'abcd'
            world=Path(d)/'world.bun';world.write_bytes(prefix+BLOB)
            out=Path(d)/'root.json'
            cmd=[sys.executable,str(Path(__file__).parent/'v44_34107_discriminator.py'),'--stream',str(world),'--offset','0xC','--expected-sha256',SOURCE_SHA,'--json',str(out)]
            completed=subprocess.run(cmd,capture_output=True,text=True)
            self.assertEqual(completed.returncode,0,completed.stderr)
            self.assertTrue(json.loads(out.read_text())['source_sha256_guard_checked'])
            self.assertEqual(world.read_bytes(),prefix+BLOB)
    def test29_cli_world_census(self):
        with tempfile.TemporaryDirectory() as d:
            world=Path(d)/'world.bun';world.write_bytes(BLOB*2)
            out=Path(d)/'census.json'
            cmd=[sys.executable,str(Path(__file__).parent/'v44_34107_discriminator.py'),'--world',str(world),'--max-roots','2','--json',str(out)]
            completed=subprocess.run(cmd,capture_output=True,text=True)
            self.assertEqual(completed.returncode,0,completed.stderr)
            self.assertEqual(json.loads(out.read_text())['counts']['both_hypotheses_true'],2)
    def test30_node_count_is_only_candidate(self):
        r=audit_root(BLOB)
        self.assertEqual(r['candidate_48byte_34105_node_count'],8)
        self.assertEqual(r['34105_candidate_node_size_bytes'],384)

if __name__=='__main__':unittest.main()
