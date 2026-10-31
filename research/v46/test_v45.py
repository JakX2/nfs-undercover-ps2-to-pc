"""V45 checks, source-backed and explicitly synthetic paired-root checks only."""
import hashlib
import json
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from v43_spatial_audit import ROOT, INFO, INST, AUX, TREE, UNKNOWN, HEADER, SOURCE_SHA, AuditError, parse_root, analyze_34105, parse_instances
from v45_scene_compat_gate import (
    opaque_34107_lane_map, stale_membership_probe, compare_v42_style_roots,
    contiguous_ranges, payload_instances,
)

HERE=Path(__file__).parent
FIXTURE=HERE/'fixtures/UC_Wii_RedBuilding_Original_Scene.chunk'
DATA=FIXTURE.read_bytes()
PARTS=parse_root(DATA)


def chunk(tag,payload):
    return struct.pack('<II',tag,len(payload))+payload


def sample_pair():
    """Construct tiny synthetic byte-contract fixtures, NOT a real Carbon PC file."""
    _pad,_flat,rows=payload_instances(DATA,PARTS)
    info=PARTS[INFO]['data']
    aux=PARTS[AUX]['data']
    order=list(PARTS)
    def make(n,edit=None):
        payloads={
            HEADER: PARTS[HEADER]['data'],
            INFO: info[:72*2]+(info[72*2:72*3] if n==3 else b''),
            AUX: aux[:32*2]+(aux[26*32:27*32] if n==3 else b''),
            TREE: PARTS[TREE]['data'],
            UNKNOWN: PARTS[UNKNOWN]['data'],
        }
        rr=list(rows[:2]);
        if n==3:
            new=bytearray(rows[26]);struct.pack_into('<h',new,0x54,2)
            rr.append(bytes(new))
        # Header comes before instance chunk. Its start always requires 4-byte alignment padding.
        payloads[INST]=b'\0'*4+b''.join(rr)
        if edit:
            key,modify=edit
            payloads[key]=modify(payloads[key])
        body=b''.join(chunk(k,payloads[k]) for k in order)
        return struct.pack('<II',ROOT,len(body))+body
    return make(2),make(3),make

class V45ReadOnlyFixture(unittest.TestCase):
    def test01_verified_sha(self):
        self.assertEqual(hashlib.sha256(DATA).hexdigest(),SOURCE_SHA)
    def test02_stale_tree_virtual_insertion_rejected(self):
        r=stale_membership_probe(DATA)
        self.assertTrue(r['unmodified_tree_rejected'])
        self.assertEqual((r['original_instances'],r['virtual_instances']),(31,32))
    def test03_virtual_insert_does_not_mutate_fixture(self):
        before=hashlib.sha256(DATA).hexdigest()
        stale_membership_probe(DATA)
        self.assertEqual(before,hashlib.sha256(FIXTURE.read_bytes()).hexdigest())
    def test04_reject_incorrect_source(self):
        with self.assertRaisesRegex(AuditError,'source fixture'):
            stale_membership_probe(DATA,'a'*64)
    def test05_num_candidate_128_blocks(self):
        self.assertEqual(opaque_34107_lane_map(PARTS[UNKNOWN]['data'])['candidate_128_byte_blocks'],24)
    def test06_number_populated(self):
        self.assertEqual(opaque_34107_lane_map(PARTS[UNKNOWN]['data'])['populated_blocks'],23)
    def test07_zero_window(self):
        self.assertTrue(opaque_34107_lane_map(PARTS[UNKNOWN]['data'])['populated_common_all_zero_window_68_to_119'])
    def test08_byte_lanes(self):
        r=opaque_34107_lane_map(PARTS[UNKNOWN]['data'])
        self.assertIn({'start':67,'end_exclusive':120,'length':53},r['zero_byte_offset_ranges'])
    def test09_all_17_first_dwords_vary(self):
        self.assertEqual(opaque_34107_lane_map(PARTS[UNKNOWN]['data'])['variable_dword_indices'],list(range(17)))
    def test10_common_footer(self):
        self.assertEqual(opaque_34107_lane_map(PARTS[UNKNOWN]['data'])['populated_footer_u32_pairs'],[(384,384)])
    def test11_unique_first68bytes(self):
        self.assertTrue(opaque_34107_lane_map(PARTS[UNKNOWN]['data'])['populated_head_68_bytes_all_unique'])
    def test12_wrong_block_stride(self):
        self.assertIsNone(opaque_34107_lane_map(b'123')['candidate_128_byte_blocks'])
    def test13_empty_payload_no_semantic_claim(self):
        self.assertTrue(opaque_34107_lane_map(b'\0'*128)['no_semantic_record_claim'])
    def test14_contiguous(self):
        self.assertEqual(contiguous_ranges([1,2,4,5,6]),[{'start':1,'end_exclusive':3,'length':2},{'start':4,'end_exclusive':7,'length':3}])

class V45SyntheticPair(unittest.TestCase):
    def setUp(self):
        self.orig,self.cand,self.make=sample_pair()
    def test15_valid_synthetic_pair(self):
        report=compare_v42_style_roots(self.orig,self.cand,source_wii=DATA)
        self.assertTrue(report['checks']['all_checked_byte_contracts_pass'],report)
        self.assertFalse(report['game_install_safe'])
    def test16_root_delta_200(self):
        self.assertEqual(len(self.cand)-len(self.orig),200)
    def test17_sha_guards(self):
        r=compare_v42_style_roots(self.orig,self.cand,expected_original_sha=hashlib.sha256(self.orig).hexdigest())
        self.assertTrue(r['checks']['all_checked_byte_contracts_pass'])
    def test18_bad_sha_guard_rejected(self):
        with self.assertRaisesRegex(AuditError,'SHA256'):
            compare_v42_style_roots(self.orig,self.cand,expected_original_sha='0'*64)
    def test19_modified_tree_detected(self):
        modified=self.make(3,(TREE,lambda x:x[:-1]+bytes([x[-1]^1])))
        r=compare_v42_style_roots(self.orig,modified)
        self.assertFalse(r['checks']['original_opaque_children_byte_identical'])
        self.assertFalse(r['checks']['all_checked_byte_contracts_pass'])
    def test20_modified_opaque_34107_detected(self):
        modified=self.make(3,(UNKNOWN,lambda x:x[:-1]+bytes([x[-1]^1])))
        self.assertFalse(compare_v42_style_roots(self.orig,modified)['checks']['original_opaque_children_byte_identical'])
    def test21_modified_old_info_detected(self):
        modified=self.make(3,(INFO,lambda x:bytes([x[0]^1])+x[1:]))
        self.assertFalse(compare_v42_style_roots(self.orig,modified)['checks']['original_72B_infos_byte_identical'])
    def test22_modified_old_instance_detected(self):
        modified=self.make(3,(INST,lambda x:x[:4]+bytes([x[4]^1])+x[5:]))
        self.assertFalse(compare_v42_style_roots(self.orig,modified)['checks']['original_96B_instances_byte_identical'])
    def test23_modified_old_aux_detected(self):
        modified=self.make(3,(AUX,lambda x:bytes([x[0]^1])+x[1:]))
        self.assertFalse(compare_v42_style_roots(self.orig,modified)['checks']['original_32B_aux_byte_identical'])
    def test24_invalid_new_info_pointer_detected(self):
        def mutate(s):
            b=bytearray(s)
            struct.pack_into('<h',b,len(b)-96+0x54,1)
            return bytes(b)
        modified=self.make(3,(INST,mutate))
        self.assertFalse(compare_v42_style_roots(self.orig,modified)['checks']['new_info_index_points_to_appended_info'])
    def test25_modified_source_placement_detected(self):
        def mutate(s):
            b=bytearray(s);b[-96]^=1
            return bytes(b)
        modified=self.make(3,(INST,mutate))
        self.assertFalse(compare_v42_style_roots(self.orig,modified,source_wii=DATA)['checks']['new_record_matches_Wii_instance26_except_info_index'])
    def test26_modified_new_aux_detected(self):
        modified=self.make(3,(AUX,lambda x:x[:-1]+bytes([x[-1]^1])))
        self.assertFalse(compare_v42_style_roots(self.orig,modified,source_wii=DATA)['checks']['new_aux_exactly_matches_Wii_instance26'])
    def test27_different_child_inventory_rejected(self):
        # Dropping opaque child, repair envelope length.
        p=parse_root(self.cand)
        body=b''.join(chunk(k,v['data']) for k,v in p.items() if k!=UNKNOWN)
        with self.assertRaisesRegex(AuditError,'inventory'):
            compare_v42_style_roots(self.orig,struct.pack('<II',ROOT,len(body))+body)
    def test28_reordered_children_rejected(self):
        p=parse_root(self.cand)
        order=list(p);order.reverse()
        body=b''.join(chunk(k,p[k]['data']) for k in order)
        with self.assertRaisesRegex(AuditError,'ordering'):
            compare_v42_style_roots(self.orig,struct.pack('<II',ROOT,len(body))+body)
    def test29_pair_report_does_not_assert_PC_schema(self):
        r=compare_v42_style_roots(self.orig,self.cand)
        self.assertFalse(r['carbon_pc_34105_schema_proven'])
        self.assertFalse(r['writer_exists'])
    def test30_reject_bad_wii_source_hash(self):
        with self.assertRaisesRegex(AuditError,'Wii source'):
            compare_v42_style_roots(self.orig,self.cand,source_wii=b'bad')

class V45CLI(unittest.TestCase):
    def test31_cli_source_protection(self):
        cmd=[sys.executable,str(HERE/'v45_scene_compat_gate.py'),'--wii-scene',str(FIXTURE),'--json',str(FIXTURE)]
        x=subprocess.run(cmd,capture_output=True,text=True)
        self.assertNotEqual(x.returncode,0)
        self.assertEqual(hashlib.sha256(FIXTURE.read_bytes()).hexdigest(),SOURCE_SHA)
    def test32_cli_report(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/'test.json'
            cmd=[sys.executable,str(HERE/'v45_scene_compat_gate.py'),'--wii-scene',str(FIXTURE),'--json',str(out)]
            x=subprocess.run(cmd,capture_output=True,text=True)
            self.assertEqual(x.returncode,0,x.stderr)
            j=json.loads(out.read_text())
            self.assertFalse(j['game_files_modified'])
    def test33_cli_report_no_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/'test.json';out.write_text('evidence')
            cmd=[sys.executable,str(HERE/'v45_scene_compat_gate.py'),'--wii-scene',str(FIXTURE),'--json',str(out)]
            x=subprocess.run(cmd,capture_output=True,text=True)
            self.assertNotEqual(x.returncode,0)
            self.assertEqual(out.read_text(),'evidence')
    def test34_cli_synthetic_pc_pair(self):
        old,new,_=sample_pair()
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);oldp=p/'orig.chunk';newp=p/'candidate.chunk';out=p/'audit.json'
            oldp.write_bytes(old);newp.write_bytes(new)
            x=subprocess.run([sys.executable,str(HERE/'v45_scene_compat_gate.py'),'--wii-scene',str(FIXTURE),
                '--original-pc',str(oldp),'--candidate-pc',str(newp),'--json',str(out)],capture_output=True,text=True)
            self.assertEqual(x.returncode,0,x.stderr)
            self.assertTrue(json.loads(out.read_text())['pc_candidate_byte_contract']['checks']['all_checked_byte_contracts_pass'])
            self.assertEqual(oldp.read_bytes(),old);self.assertEqual(newp.read_bytes(),new)

if __name__=='__main__':unittest.main()
