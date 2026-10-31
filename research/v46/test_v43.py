"""Source-backed corruption and invariant tests for the V43 READ-ONLY analyzer."""
import hashlib
import struct
import tempfile
import unittest
from pathlib import Path

from v43_world_census import census_stream
from v43_spatial_audit import (ROOT, SOURCE_SHA, INST, TREE, UNKNOWN, AUX,
    AuditError, analyze_scene, parse_root, analyze_34107, dot_tree, read_root_from_stream)

HERE = Path(__file__).resolve().parent
SOURCE = (HERE/'fixtures/UC_Wii_RedBuilding_Original_Scene.chunk').read_bytes()
PARTS = parse_root(SOURCE)
TREE_START = PARTS[TREE]['payload_offset']
INST_START = (PARTS[INST]['payload_offset'] + 15)&-16


def mutation(pos, replacement):
    data=bytearray(SOURCE)
    data[pos:pos+len(replacement)]=replacement
    return bytes(data)


def patch_node(node, local, replacement):
    return mutation(TREE_START+48*node+local, replacement)


class SourceEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result=analyze_scene(SOURCE,expected_sha=SOURCE_SHA,strict_tree=True)

    def test_fixture_sha256(self):
        self.assertEqual(hashlib.sha256(SOURCE).hexdigest(),SOURCE_SHA)

    def test_scene_and_instance_count(self):
        self.assertEqual(self.result['instance_count'],31)
        self.assertEqual(self.result['root_total_bytes'],8488)
        self.assertEqual([x['tag'] for x in self.result['child_chunks']],
                         ['0x00034101','0x00034103','0x00034102',
                          '0x0003410D','0x00034105','0x00034107'])

    def test_node_count_and_coverage(self):
        tree=self.result['spatial_34105']
        self.assertEqual(tree['node_count'],8)
        self.assertEqual(tree['record_width'],48)
        self.assertEqual(tree['root_instance_count'],31)
        self.assertTrue(tree['all_instances_referenced_exactly_once'])
        self.assertTrue(tree['all_nonroot_nodes_referenced_exactly_once'])
        self.assertEqual(sorted(sum([node['refs'] for node in tree['nodes']],[])),
                         list(range(-7,0))+list(range(31)))

    def test_parent_child_relations(self):
        nodes=self.result['spatial_34105']['nodes']
        self.assertEqual(nodes[0]['refs'],[6,-2,-1])
        self.assertEqual(nodes[1]['refs'],[1,-5,-4,30,-3])
        self.assertEqual(nodes[2]['refs'],[26,5,3,29,2])
        self.assertEqual(nodes[3]['refs'],[0,16,-7,21,-6])
        self.assertEqual(self.result['instance26_direct_parent_nodes'],[2])
        self.assertEqual(self.result['instance26_containing_nodes'],[0,2])

    def test_all_node_box_unions_match_exactly(self):
        for n in self.result['spatial_34105']['nodes']:
            self.assertTrue(n['bounds_match_exact_instance_union'])

    def test_aux_not_reinterpreted(self):
        self.assertTrue(self.result['3410D_size_per_instance_32'])
        self.assertEqual(PARTS[AUX]['payload_size'],31*32)

    def test_34107_observations_only(self):
        o=self.result['opaque_34107']
        self.assertEqual(o['payload_size'],3072)
        self.assertEqual(o['initial_zero_bytes'],129)
        self.assertEqual(o['nonzero_bytes'],607)
        self.assertEqual(o['observed_strides_without_semantic_claim']['128']['row_count'],24)
        self.assertEqual(o['observed_strides_without_semantic_claim']['128']['distinct_rows'],24)
        self.assertTrue(o['size_equal_to_instances_plus_one_times_96'])
        self.assertIn('opaque',o['state'])
        self.assertTrue(o['must_preserve_bytes'])
        self.assertFalse(self.result['carbon_pc_runtime_schema_verified'])
        self.assertFalse(self.result['model_placement_patch_ready'])

    def test_graph_diagram(self):
        dot=dot_tree(self.result)
        self.assertIn('n0 -> n1;',dot)
        self.assertIn('n0 -> n2;',dot)
        self.assertIn('n2 -> inst26;',dot)
        self.assertEqual(dot.count(' [shape=ellipse'),31)

    def test_fingerprint_guard(self):
        with self.assertRaisesRegex(AuditError,'fingerprint'):
            analyze_scene(SOURCE[:-1]+bytes([SOURCE[-1]^1]),expected_sha=SOURCE_SHA)

    def test_no_spatial_claim_without_tree(self):
        bad=patch_node(0,12,struct.pack('<H',11))
        r=analyze_scene(bad,strict_tree=False)
        self.assertIsNone(r['spatial_34105'])
        self.assertEqual(r['spatial_34105_verification'],'not established for this file')

    def test_reject_node_count_out_of_bounds(self):
        with self.assertRaisesRegex(AuditError,'capacity'):
            analyze_scene(patch_node(0,12,struct.pack('<H',11)),strict_tree=True)

    def test_reject_node_reserved_nonzero(self):
        with self.assertRaisesRegex(AuditError,'unknown layout'):
            analyze_scene(patch_node(0,14,struct.pack('<H',1)),strict_tree=True)

    def test_reject_node_unused_nonzero(self):
        with self.assertRaisesRegex(AuditError,'trailing'):
            analyze_scene(patch_node(0,34,b'\x01'),strict_tree=True)

    def test_reject_node_invalid_instance(self):
        with self.assertRaisesRegex(AuditError,'nonexistent instance'):
            analyze_scene(patch_node(2,28,struct.pack('<h',31)),strict_tree=True)

    def test_reject_node_invalid_child(self):
        with self.assertRaisesRegex(AuditError,'nonexistent child'):
            analyze_scene(patch_node(0,30,struct.pack('<h',-8)),strict_tree=True)

    def test_reject_self_cycle(self):
        with self.assertRaisesRegex(AuditError,'Cycle'):
            analyze_scene(patch_node(1,30,struct.pack('<h',-1)),strict_tree=True)

    def test_reject_instance_duplicated(self):
        with self.assertRaisesRegex(AuditError,'coverage'):
            analyze_scene(patch_node(2,28,struct.pack('<h',5)),strict_tree=True)

    def test_reject_node_bbox_mutated(self):
        with self.assertRaisesRegex(AuditError,'bounding box differs'):
            analyze_scene(patch_node(2,0,struct.pack('<f',2594.5)),strict_tree=True)

    def test_reject_instance_bbox_mutated(self):
        with self.assertRaisesRegex(AuditError,'bounding box differs'):
            analyze_scene(mutation(INST_START+26*96+16,struct.pack('<f',10000.0)),strict_tree=True)

    def test_reject_instance_inverted_bbox(self):
        with self.assertRaisesRegex(AuditError,'Invalid instance AABB'):
            analyze_scene(mutation(INST_START+26*96,struct.pack('<f',10000.0)),strict_tree=True)

    def test_reject_root_tag_mutation(self):
        with self.assertRaisesRegex(AuditError,'Scene root'):
            analyze_scene(mutation(0,struct.pack('<I',0x80034101)))

    def test_reject_root_length_mutation(self):
        with self.assertRaisesRegex(AuditError,'Scene root'):
            analyze_scene(mutation(4,struct.pack('<I',3)))

    def test_reject_duplicate_child_tag(self):
        with self.assertRaisesRegex(AuditError,'Duplicate'):
            analyze_scene(mutation(PARTS[0x34102]['chunk_offset'],struct.pack('<I',INST)))

    def test_reject_missing_inst(self):
        with self.assertRaisesRegex(AuditError,'No 0x34103'):
            analyze_scene(mutation(PARTS[INST]['chunk_offset'],struct.pack('<I',0x34104)))

    def test_reject_truncated_child(self):
        with self.assertRaisesRegex(AuditError,'Child extends'):
            analyze_scene(mutation(PARTS[UNKNOWN]['chunk_offset']+4,struct.pack('<I',999999)))

    def test_run_with_opaque_payload_mutation_is_not_labeled_verified(self):
        changed=mutation(PARTS[UNKNOWN]['payload_offset']+200,b'\x23')
        r=analyze_scene(changed,strict_tree=True)
        self.assertTrue(r['spatial_34105']['all_node_aabbs_equal_instance_unions'])
        self.assertFalse(r['carbon_pc_runtime_schema_verified'])
        self.assertNotEqual(r['opaque_34107']['sha256'],self.result['opaque_34107']['sha256'])

    def test_synthetic_world_census(self):
        opaque=struct.pack('<II',0x80000001,4)+b'ABCD'
        world=opaque+SOURCE+opaque+SOURCE
        summary=census_stream(world,max_samples=5)
        self.assertEqual(summary['counts']['top_level_chunks'],4)
        self.assertEqual(summary['counts']['scene_roots'],2)
        self.assertEqual(summary['counts']['roots_with_exact_48B_tree_and_bbox_membership'],2)
        self.assertEqual(summary['counts']['roots_with_34107'],2)
        self.assertEqual(summary['34107_instance_count_vs_length'],[{'instances':31,'opaque_bytes':3072,'roots':2}])
        self.assertEqual([r['root_stream_offset'] for r in summary['samples']], ['0xC','0x2140'])
        self.assertTrue(summary['never_writes_to_game_stream'])

    def test_census_cutoff(self):
        world=SOURCE+SOURCE
        summary=census_stream(world,max_roots=1)
        self.assertEqual(summary['counts']['scene_roots'],1)
        self.assertLess(summary['bytes_traversed'],len(world))

    def test_census_invalid_framing(self):
        with self.assertRaisesRegex(AuditError,'truncated'):
            census_stream(SOURCE+b'\x01\x02')

    def test_read_only_stream_offset(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'synthetic_bun.bin'
            original=bytes(32)+SOURCE+bytes(64)
            p.write_bytes(original)
            self.assertEqual(read_root_from_stream(p,32),SOURCE)
            self.assertEqual(p.read_bytes(),original)
            with self.assertRaisesRegex(AuditError,'Expected root'):
                read_root_from_stream(p,0)
            with self.assertRaisesRegex(AuditError,'outside original stream'):
                read_root_from_stream(p,len(original))


if __name__=='__main__':unittest.main()
