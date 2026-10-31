"""Asset-free V54 tests; optional original Wii fixture needs NFS_UC_WII_SCENE.

Never writes game assets. No third-party packages.
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
import v54_spatial_robustness_gate as v54
v53=v54.v53
v50=v54.v50


def samples():
    ids=[0,1,2,3,4]
    positions={i:(float(i*i), float(i*3),0.) for i in ids}
    masks=[frozenset(range(i+1))|frozenset((30,40)) for i in ids]
    return ids,positions,masks


def synthetic_root():
    # Same zero position safety conditions as existing v53 synthetic case.
    parts=[(v50.SCENE,b'\x00'*68)]
    payload_offset=8+8+68+8
    pad=(-payload_offset)&15
    rows=[]
    for i in range(5):
        b=bytearray(96); xyz=(float(4+i*7),float(i*2),0.)
        struct.pack_into('<3f',b,0,*tuple(x-1 for x in xyz))
        struct.pack_into('<3f',b,16,*tuple(x+1 for x in xyz))
        struct.pack_into('<h',b,28,i+1)
        struct.pack_into('<3f',b,32,*xyz)
        struct.pack_into('<h',b,84,6 if i<4 else 8)
        rows.append(bytes(b))
    parts.append((v50.INSTANCE,b'\x11'*pad+b''.join(rows)))
    parts.append((v50.AUX,bytes(32*5)))
    blocks=[]
    for i in range(6):
        b=bytearray(128);b[:4]=bytes((min(i,8),i*2,i*3,i*4));blocks.append(bytes(b))
    parts.append((v50.PRECULLER,b''.join(blocks)))
    body=b''.join(struct.pack('<II',t,len(data))+data for t,data in parts)
    return struct.pack('<II',v50.ROOT,len(body))+body


class AssetFreeTests(unittest.TestCase):
    def setUp(self):
        self.ids,self.positions,self.masks=samples()

    def test_stable_shared_bits(self):
        self.assertEqual(set.intersection(*(set(x) for x in self.masks)),{0,30,40})

    def test_spearman_defined(self):
        p=v54._prepare(self.ids,self.positions,self.masks)
        self.assertEqual(p[4],v53.spearman(p[2],p[3]))

    def test_drop_common_reports_count(self):
        p=v54._prepare(self.ids,self.positions,self.masks,remove_shared_bits=True)
        self.assertEqual(p[5],3)

    def test_drop_common_does_not_modify_masks(self):
        orig=list(self.masks)
        v54._prepare(self.ids,self.positions,self.masks,remove_shared_bits=True)
        self.assertEqual(self.masks,orig)

    def test_leave_one_out_count(self):
        x=v54.leave_one_block_out(self.ids,self.positions,self.masks)
        self.assertEqual(len(x['influence']),5)
        self.assertEqual([r['removed_candidate_block'] for r in x['influence']],self.ids)

    def test_leave_one_out_baseline_matches_pairwise(self):
        x=v54.leave_one_block_out(self.ids,self.positions,self.masks)
        self.assertAlmostEqual(x['baseline_rho'],v54._prepare(self.ids,self.positions,self.masks)[4])

    def test_leave_one_out_shared_bits_fixed(self):
        x=v54.leave_one_block_out(self.ids,self.positions,self.masks,remove_shared_bits=True)
        self.assertEqual(x['feature_shared_bits_removed_in_baseline'],3)
        self.assertEqual(len(x['influence']),5)

    def test_permutation_reproducible(self):
        a=v54.within_group_permutation(self.ids,self.positions,self.masks,[0,1,2],permutations=97,seed=18)
        b=v54.within_group_permutation(self.ids,self.positions,self.masks,[0,1,2],permutations=97,seed=18)
        self.assertEqual(a,b)

    def test_permutation_counts_within_range(self):
        x=v54.within_group_permutation(self.ids,self.positions,self.masks,[0,1,2],permutations=97)
        self.assertGreaterEqual(x['one_sided_extreme_count'],0)
        self.assertLessEqual(x['one_sided_extreme_count'],97)
        self.assertEqual(x['other_candidate_mask_labels_fixed'],2)

    def test_permutation_zero_has_no_p_value(self):
        x=v54.within_group_permutation(self.ids,self.positions,self.masks,[0,1,2],permutations=0)
        self.assertIsNone(x['one_sided_p_plus_one'])

    def test_permutation_shared_bits_recomputed(self):
        x=v54.within_group_permutation(self.ids,self.positions,self.masks,[0,1,2],permutations=17,remove_shared_bits=True)
        self.assertEqual(x['common_mask_bits_removed'],3)

    def test_reject_duplicate_ids(self):
        with self.assertRaisesRegex(v50.EvidenceError,'distinct'):
            v54.leave_one_block_out([0,1,1,2],self.positions,self.masks)

    def test_reject_short_sample(self):
        with self.assertRaises(v50.EvidenceError):
            v54.leave_one_block_out([0,1,2],self.positions,self.masks)

    def test_reject_unknown_id(self):
        with self.assertRaises(v50.EvidenceError):
            v54.leave_one_block_out([0,1,2,9],self.positions,self.masks)

    def test_reject_nan_position(self):
        p=dict(self.positions);p[1]=(float('nan'),0.,0.)
        with self.assertRaises(v50.EvidenceError):
            v54.leave_one_block_out(self.ids,p,self.masks)

    def test_reject_few_movable(self):
        with self.assertRaisesRegex(v50.EvidenceError,'3+'):
            v54.within_group_permutation(self.ids,self.positions,self.masks,[1,2],permutations=9)

    def test_reject_duplicate_movable(self):
        with self.assertRaises(v50.EvidenceError):
            v54.within_group_permutation(self.ids,self.positions,self.masks,[1,1,2],permutations=9)

    def test_reject_movable_outside_ids(self):
        with self.assertRaises(v50.EvidenceError):
            v54.within_group_permutation(self.ids,self.positions,self.masks,[1,2,9],permutations=9)

    def test_reject_negative_permutations(self):
        with self.assertRaises(v50.EvidenceError):
            v54.within_group_permutation(self.ids,self.positions,self.masks,[1,2,3],permutations=-1)

    def test_reject_excessive_permutations(self):
        with self.assertRaises(v50.EvidenceError):
            v54.within_group_permutation(self.ids,self.positions,self.masks,[1,2,3],permutations=100001)

    def test_root_guard(self):
        with self.assertRaisesRegex(v50.EvidenceError,'SHA-256'):
            v54.audit(synthetic_root(),expected_sha256='0'*64,permutations=5)

    def test_synthetic_audit_not_original(self):
        x=v54.audit(synthetic_root(),expected_sha256=v50.sha256(synthetic_root()),permutations=11)
        self.assertEqual(x['source_authentication'],'unknown')
        self.assertFalse(x['Carbon_PC_serialized_schema_proven'])
        self.assertFalse(x['safe_to_install'])
        self.assertEqual(x['cohort_info6_blocks'],4)

    def test_uniqueness_duplicate_is_not_replication(self):
        b=synthetic_root();x=v54.source_uniqueness_gate(b,[b],[v50.sha256(b)])
        self.assertEqual(x['distinct_root_sha256s'],1)
        self.assertFalse(x['at_least_two_distinct_roots'])
        self.assertFalse(x['independent_original_scenes_authenticated'])

    def test_uniqueness_different_hashes_not_proven_original(self):
        a=synthetic_root();b=a[:-1]+bytes([a[-1]^1])
        x=v54.source_uniqueness_gate(a,[b],[v50.sha256(b)])
        self.assertEqual(x['distinct_root_sha256s'],2)
        self.assertTrue(x['at_least_two_distinct_roots'])
        self.assertFalse(x['independent_original_scenes_authenticated'])

    def test_uniqueness_bad_fingerprint_rejected(self):
        with self.assertRaises(v50.EvidenceError):
            v54.source_uniqueness_gate(synthetic_root(),[synthetic_root()],['a'*64])

    def test_uniqueness_mismatched_count_rejected(self):
        with self.assertRaises(v50.EvidenceError):
            v54.source_uniqueness_gate(synthetic_root(),[synthetic_root()],[])

    def test_cli_guard_against_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'scene.chunk';p.write_bytes(synthetic_root())
            completed=subprocess.run([sys.executable,str(Path(v54.__file__)),'--scene',str(p),
                '--expected-root-sha256',v50.sha256(p.read_bytes()),'--report',str(p)],
                capture_output=True,text=True)
            self.assertNotEqual(completed.returncode,0)
            self.assertIn('Refusing overwrite',completed.stderr)

    def test_cli_output_on_fresh_path(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'scene.chunk';p.write_bytes(synthetic_root())
            out=Path(d)/'audit.json'
            completed=subprocess.run([sys.executable,str(Path(v54.__file__)),'--scene',str(p),
                '--expected-root-sha256',v50.sha256(p.read_bytes()),'--permutations','9',
                '--report',str(out)],capture_output=True,text=True)
            self.assertEqual(completed.returncode,0,completed.stderr)
            self.assertFalse(json.loads(out.read_text())['in_game_verified'])
            self.assertEqual(json.loads(out.read_text())['source_uniqueness']['distinct_root_sha256s'],1)


class PinnedWiiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        file=os.environ.get('NFS_UC_WII_SCENE')
        if not file or not Path(file).is_file():raise unittest.SkipTest('Authorized original Wii fixture absent')
        cls.data=Path(file).read_bytes()
        if v50.sha256(cls.data)!=v54.KNOWN_WII_SHA:raise unittest.SkipTest('Fixture does not match pinned original Wii SHA')
        cls.report=v54.audit(cls.data,expected_sha256=v54.KNOWN_WII_SHA,permutations=9999,seed=540)

    def test_scene_has_22_nonzero_position_candidate_blocks(self):
        self.assertEqual(self.report['candidate_nonzero_position_blocks'],22)

    def test_cohort_has_13_masks(self):
        self.assertEqual(self.report['cohort_info6_blocks'],13)

    def test_all_mask_rho_matches_v53(self):
        self.assertAlmostEqual(self.report['all_nonzero_block_jackknife']['baseline_rho'],-0.5900183685298409,places=10)

    def test_loo_all_remains_negative(self):
        x=self.report['all_nonzero_block_jackknife']
        self.assertEqual(len(x['influence']),22)
        self.assertTrue(x['all_jackknife_rhos_negative'])

    def test_loo_info6_remains_negative(self):
        x=self.report['info6_cohort_jackknife']
        self.assertEqual(len(x['influence']),13)
        self.assertTrue(x['all_jackknife_rhos_negative'])

    def test_group_shuffle_source6_only(self):
        x=self.report['group_locked_permutation']
        self.assertEqual(x['cohort_movable_block_count'],13)
        self.assertEqual(x['other_candidate_mask_labels_fixed'],9)
        self.assertEqual(x['one_sided_extreme_count'],0)
        self.assertEqual(x['one_sided_p_plus_one'],0.0001)

    def test_group_shuffle_remove_shared_bits(self):
        x=self.report['group_locked_permutation_without_shared_bits']
        self.assertAlmostEqual(x['rho'],-0.5680446514634487,places=10)
        self.assertEqual(x['one_sided_extreme_count'],0)

    def test_source_uniqueness_one_only(self):
        x=self.report['source_uniqueness']
        self.assertEqual(x['sources_submitted'],1)
        self.assertEqual(x['distinct_root_sha256s'],1)
        self.assertFalse(x['independent_original_scenes_authenticated'])

if __name__=='__main__':unittest.main()