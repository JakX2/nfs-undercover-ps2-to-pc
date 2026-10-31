"""V53 asset-free tests and optional authentic source-backed Wii tests.

Original game bytes MUST stay local, referenced only via NFS_UC_WII_SCENE.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parent))
import v53_preculler_spatial_controls as v53
v50=v53.v50


def root(rows=None,masks=None):
    if rows is None:rows=[(1,(1.,1.,1.)),(2,(10.,1.,1.)),(3,(22.,1.,1.)),(4,(40.,1.,1.))]
    if masks is None:masks=[b'',b'\x01',b'\x03',b'\x07',b'\x0f']
    parts=[(v50.SCENE,b'\0'*68)]
    count_bytes=sum(8+len(payload) for _,payload in parts)
    start=8+count_bytes+8
    pad=(-start)&15
    entries=[]
    for idx,(group,xyz) in enumerate(rows):
        b=bytearray(96)
        mn=tuple(x-1. for x in xyz);mx=tuple(x+1. for x in xyz)
        struct.pack_into('<3f',b,0,*mn)
        struct.pack_into('<3f',b,16,*mx)
        struct.pack_into('<h',b,28,group)
        struct.pack_into('<3f',b,32,*xyz)
        struct.pack_into('<h',b,84,6)
        entries.append(bytes(b))
    payload=b'\x11'*pad+b''.join(entries)
    chunks=[]
    for v in masks:
        b=bytearray(128)
        if len(v)>68:raise ValueError('too many mask bytes')
        b[:len(v)]=v
        chunks.append(bytes(b))
    parts += [(v50.INSTANCE,payload),(v50.AUX,b'\0'*(32*len(rows))),
              (v50.PRECULLER,b''.join(chunks))]
    body=b''.join(struct.pack('<II',tag,len(p))+p for tag,p in parts)
    return struct.pack('<II',v50.ROOT,len(body))+body


class PureTests(unittest.TestCase):
    def test_rank_distinct(self):
        self.assertEqual(v53.rank_average([30.,10.,20.]),[3.,1.,2.])

    def test_rank_average_tied_values(self):
        self.assertEqual(v53.rank_average([10,10,20,30,30]),[1.5,1.5,3,4.5,4.5])

    def test_rank_empty(self):
        self.assertEqual(v53.rank_average([]),[])

    def test_pearson_exact_negative(self):
        self.assertAlmostEqual(v53.pearson([1.,2.,3.],[4.,3.,2.]),-1.)

    def test_spearman_exact_negative_with_ties(self):
        self.assertAlmostEqual(v53.spearman([1,1,3,4],[4,4,2,1]),-1.)

    def test_undefined_pearson(self):
        self.assertIsNone(v53.pearson([1.,1.,1.],[1.,2.,3.]))
        self.assertIsNone(v53.pearson([1.],[1.]))

    def test_lsb_bit_indexing(self):
        self.assertEqual(v53.bits_lsb(b'\x80\x01'),frozenset({7,8}))

    def test_jaccard_empty(self):
        self.assertEqual(v53.jaccard(frozenset(),frozenset()),1.)

    def test_jaccard(self):
        self.assertEqual(v53.jaccard(frozenset({1,2}),frozenset({2,3})),1/3)

    def test_structural_synthetic_root(self):
        b=root()
        ch=v50.children_of(b)
        rows=v53.read_instances(b,ch)
        self.assertEqual(len(rows),4)
        self.assertEqual(len(v53.candidate_masks(ch)),5)
        self.assertEqual([r['preculler'] for r in rows],[1,2,3,4])

    def test_source_fingerprint_guard(self):
        b=root()
        with self.assertRaises(v50.EvidenceError):v53.audit(b,expected_sha256='0'*64)

    def test_uncertain_provenance_and_safety(self):
        j=v53.audit(root(),permutations=0)
        self.assertEqual(j['source_provenance'],'unknown')
        self.assertFalse(j['carbon_pc_serialized_schema_verified'])
        self.assertFalse(j['in_game_verified'])
        self.assertFalse(j['safe_to_install'])

    def test_disallow_negative_permutation_count(self):
        with self.assertRaises(v50.EvidenceError):v53.audit(root(),permutations=-1)

    def test_reject_out_of_range_candidate_index(self):
        with self.assertRaises(v50.EvidenceError):v53.audit(root(rows=[(10,(1.,2.,3.))]))

    def test_synthetic_zero_source_position_proxy(self):
        b=root(rows=[(1,(0.,0.,0.)),(2,(10.,1.,1.)),(3,(22.,1.,1.)),(4,(40.,1.,1.))])
        j=v53.audit(b,permutations=0)
        self.assertEqual(j['zero_position_instance_slots'],[0])
        self.assertEqual(j['nonzero_mask_blocks_with_zero_position_rows'],[1])
        self.assertEqual(j['zero_position_instance_aabb_midpoints']['0'],[0.,0.,0.])

    def test_zero_source_can_have_nonzero_aabb(self):
        b=bytearray(root(rows=[(1,(0.,0.,0.)),(2,(10.,1.,1.)),(3,(22.,1.,1.)),(4,(40.,1.,1.))]))
        ch=v50.children_of(b)
        start=ch[v50.INSTANCE][0];pad=(-start)&15
        struct.pack_into('<3f',b,start+pad,10.,20.,30.)
        struct.pack_into('<3f',b,start+pad+16,12.,22.,32.)
        j=v53.audit(bytes(b),permutations=0)
        self.assertEqual(j['zero_position_instance_aabb_midpoints']['0'],[11.,21.,31.])

    def test_mantel_reproducible(self):
        x=v53.audit(root(),permutations=37,seed=19)
        y=v53.audit(root(),permutations=37,seed=19)
        self.assertEqual(x['analysis'],y['analysis'])

    def test_mantel_counts_valid(self):
        r=v53.audit(root(),permutations=49,seed=9)
        for value in r['analysis'].values():
            p=value['label_permutation']['one_sided_p_plus_one']
            self.assertTrue(1/50 <= p <= 1)
            self.assertEqual(value['induced_pairs_not_independent'],value['blocks_compared']*(value['blocks_compared']-1)//2)

    def test_shared_bit_exclusion(self):
        b=root()
        ch=v50.children_of(b);m=v53.candidate_masks(ch)
        ids=[1,2,3,4]
        loc=v53.centroids(v53.read_instances(b,ch),ids,mode='raw_position')
        x=v53.paired_statistics(ids,loc,m,drop_common=True)
        self.assertTrue(x['similarity_excludes_shared_bits'])
        self.assertEqual(x['shared_bit_positions_removed'],1)

    def test_three_points_minimum(self):
        with self.assertRaises(v50.EvidenceError):
            v53.paired_statistics([0,1],{0:(0,0,0),1:(1,2,3)},[frozenset({1}),frozenset({2})])

    def test_invalid_aabb_rejected(self):
        b=bytearray(root());ch=v50.children_of(b);start=ch[v50.INSTANCE][0]
        struct.pack_into('<f',b,start+((-start)&15),12345.)
        with self.assertRaises(v50.EvidenceError):v53.audit(bytes(b))

    def test_cli_no_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            source=Path(temp)/'original.chunk';out=Path(temp)/'report.json'
            source.write_bytes(root())
            with patch.object(sys,'argv',['prog','--scene',str(source),'--report',str(out),'--permutations','0']):v53.main()
            with patch.object(sys,'argv',['prog','--scene',str(source),'--report',str(out),'--permutations','0']):
                with self.assertRaises(SystemExit):v53.main()

    def test_input_bytes_unchanged(self):
        b=root(); v53.audit(b,permutations=23);self.assertEqual(b,root())


class OriginalWiiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        filename=os.getenv('NFS_UC_WII_SCENE','')
        if not filename or not Path(filename).is_file():raise unittest.SkipTest('Private Wii fixture not supplied')
        cls.blob=Path(filename).read_bytes()
        if hashlib.sha256(cls.blob).hexdigest()!=v53.KNOWN_WII_SHA:
            raise unittest.SkipTest('Wii source fixture SHA mismatch')
        cls.report=v53.audit(cls.blob,expected_sha256=v53.KNOWN_WII_SHA,permutations=999,seed=533)

    def test_exact_source(self):
        self.assertEqual(len(self.blob),8488)
        self.assertEqual(self.report['source_provenance'],'exact_original_Wii_RedBuilding')

    def test_four_opaque_zero_positions(self):
        self.assertEqual(self.report['zero_position_instance_slots'],[0,1,2,30])
        self.assertEqual(self.report['zero_position_block_ids'],[0,1])

    def test_zero_positions_nonzero_aabb(self):
        for location in self.report['zero_position_instance_aabb_midpoints'].values():
            self.assertGreater(location[0],2400)
            self.assertGreater(location[1],3000)

    def test_wii_flags_differ(self):
        flags=self.report['zero_position_instance_flags']
        self.assertEqual([flags[str(i)] for i in (0,1,2,30)],['0x000006C0']*3+['0x00000400'])

    def test_previous_far_distance_example_is_bad(self):
        self.assertFalse(self.report['previous_v52_far_apart_pair_1_11_valid_geographic_counterexample'])
        self.assertEqual(self.report['nonzero_mask_blocks_with_zero_position_rows'],[1])

    def test_actual_source_correlation_controls(self):
        x=self.report['analysis']
        self.assertAlmostEqual(x['all_raw_source_positions']['spearman_distance_vs_similarity'],-0.4744973366068971,places=8)
        self.assertAlmostEqual(x['exclude_zero_position_groups']['spearman_distance_vs_similarity'],-0.590018368529841,places=8)
        self.assertAlmostEqual(x['aabb_center_proxy_for_zero_position_groups']['spearman_distance_vs_similarity'],-0.5817388688551663,places=8)
        self.assertAlmostEqual(x['exclude_zero_positions_and_shared_mask_bits']['spearman_distance_vs_similarity'],-0.568045,places=5)

    def test_separate_info_six_cohort(self):
        x=self.report['analysis']['source_scenery_info_6_only']
        self.assertEqual(x['blocks_compared'],13)
        self.assertLess(x['spearman_distance_vs_similarity'],-0.75)

    def test_permutation_one_sided_bound_and_safety(self):
        for x in self.report['analysis'].values():
            self.assertLessEqual(x['label_permutation']['one_sided_p_plus_one'],0.01)
        self.assertFalse(self.report['safe_to_install'])
        self.assertFalse(self.report['carbon_pc_serialized_schema_verified'])

if __name__=='__main__':unittest.main()