"""V56 candidate graph tests: self-contained synthetics and optional original Wii.

For authenticated local owner-provided original fixture only, set
NFS_UC_WII_SCENE to its absolute path. Never distribute source game bytes.
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
import v56_cross_root_semantic_gate as v56
v55=v56.prior


def fixture(n=3,blocks=3,endian='little',scene_len=68,info=True,aux=True,tree=True,prec=True,
            bad_instance=None,bad_prec=None,bad_info=None,bad_tree=None,extra=b''):
    e=v55.endian(endian)
    chunks=[(v55.SCENE,bytes(scene_len))]
    instance_offset=8+(8+scene_len)+8
    pad=(-instance_offset)&15
    rows=[]
    for i in range(n):
        b=bytearray(96)
        struct.pack_into(e+'3f',b,0,-1.,-2.,-3.)
        struct.pack_into(e+'3f',b,16,1.,2.,3.)
        struct.pack_into(e+'h',b,28,(i%blocks if blocks else 0) if bad_prec is None else bad_prec)
        struct.pack_into(e+'3f',b,32,5.+i,6.+i,7.+i)
        struct.pack_into(e+'h',b,84,0 if bad_info is None else bad_info)
        if bad_instance=='nan' and i==0:struct.pack_into(e+'f',b,0,float('nan'))
        if bad_instance=='reversed' and i==0:struct.pack_into(e+'f',b,0,500.)
        rows.append(bytes(b))
    chunks.append((v55.INSTANCE,b'\x11'*pad+b''.join(rows)+extra))
    if info:chunks.append((v56.INFO,bytes(72)))
    if aux:chunks.append((v55.AUX,bytes(n*32)))
    if tree:
        b=bytearray(48)
        struct.pack_into(e+'3f',b,0,-1.,-2.,-3.)
        struct.pack_into(e+'3f',b,16,1.,2.,3.)
        struct.pack_into(e+'H',b,12,n)
        for i in range(n):struct.pack_into(e+'h',b,28+2*i,i)
        if bad_tree=='coverage':struct.pack_into(e+'h',b,28+2*(n-1),0)
        if bad_tree=='aabb':struct.pack_into(e+'f',b,0,-100.)
        if bad_tree=='ref':struct.pack_into(e+'h',b,28,n+2)
        if bad_tree=='count':struct.pack_into(e+'H',b,12,11)
        if bad_tree=='cycle':struct.pack_into(e+'h',b,28,-1)
        chunks.append((v55.TREE,bytes(b)))
    if prec:chunks.append((v55.PRECULL,bytes(blocks*128)))
    payload=b''.join(struct.pack(e+'II',k,len(b))+b for k,b in chunks)
    return struct.pack(e+'II',v55.ROOT,len(payload))+payload


def audit(raw,order='little',label='synthetic'):
    parsed=v55.children(raw,order)
    meta={'label':label,'root_sha256':v55.sha256(raw),'file_sha256':v55.sha256(raw),
          'endian':order,'platform_hint_unverified':'wii','stream_offset':None}
    return v56.audit_one(raw,parsed,meta)


def replace_tree_payload(raw:bytes,tree_payload:bytes,endian='little') -> bytes:
    """Replace one synthetic source child, preserving all other chunk bytes."""
    e=v55.endian(endian)
    position=8
    chunks=[]
    replaced=False
    while position<len(raw):
        tag,length=struct.unpack_from(e+'II',raw,position)
        payload=raw[position+8:position+8+length]
        if tag==v55.TREE:
            payload=tree_payload
            replaced=True
        chunks.append(struct.pack(e+'II',tag,len(payload))+payload)
        position+=8+length
    if not replaced:raise AssertionError('source tree child absent')
    payload=b''.join(chunks)
    return struct.pack(e+'II',v55.ROOT,len(payload))+payload


def chain_tree(node_count:int,*,root_child_override=None,endian='little')->bytes:
    """Synthetic linear candidate hierarchy, one leaf, constant exact AABBs."""
    e=v55.endian(endian)
    b=bytearray(node_count*48)
    for i in range(node_count):
        off=i*48
        struct.pack_into(e+'3f',b,off,-1.,-2.,-3.)
        struct.pack_into(e+'3f',b,off+16,1.,2.,3.)
        struct.pack_into(e+'H',b,off+12,1)
        ref=-(i+1) if i<node_count-1 else 0
        if i==0 and root_child_override is not None:ref=root_child_override
        struct.pack_into(e+'h',b,off+28,ref)
    return bytes(b)


class Synthetic(unittest.TestCase):
    def test_good_exact_structural_candidate(self):
        r=audit(fixture());self.assertEqual(r['candidate_wii_graph_status'],'candidate_internally_consistent')
        self.assertFalse(r['safe_to_install']);self.assertFalse(r['carbon_pc_abi_proven'])
    def test_good_96_48_128_all_sizes(self):
        r=audit(fixture());self.assertTrue(r['candidate_size_hypotheses']['length_equals_instance_plus_one_times_96'])
        self.assertTrue(r['candidate_size_hypotheses']['length_equals_tree_nodes_times_384'])
    def test_false_positive_size_only_preculler(self):
        r=audit(fixture(bad_prec=99));self.assertTrue(r['candidate_size_hypotheses']['length_equals_tree_nodes_times_384'])
        self.assertEqual(r['candidate_wii_graph_status'],'rejected');self.assertIn('preculler',r['candidate_rejection_reason'])
    def test_false_positive_size_only_tree_coverage(self):
        r=audit(fixture(bad_tree='coverage'));self.assertTrue(r['candidate_size_hypotheses']['length_equals_tree_nodes_times_384'])
        self.assertEqual(r['candidate_wii_graph_status'],'rejected');self.assertIn('cover',r['candidate_rejection_reason'])
    def test_false_positive_size_only_tree_aabb(self):
        r=audit(fixture(bad_tree='aabb'));self.assertTrue(r['candidate_size_hypotheses']['length_equals_tree_nodes_times_384'])
        self.assertIn('AABB',r['candidate_rejection_reason'])
    def test_tree_reference_out_of_range(self):
        self.assertIn('nonexistent',audit(fixture(bad_tree='ref'))['candidate_rejection_reason'])
    def test_tree_node_arity_limit(self):
        self.assertIn('count',audit(fixture(bad_tree='count'))['candidate_rejection_reason'])
    def test_tree_child_self_cycle_or_out_of_range(self):
        self.assertEqual(audit(fixture(bad_tree='cycle'))['candidate_wii_graph_status'],'rejected')
    def test_instance_nan(self):
        self.assertIn('non-finite',audit(fixture(bad_instance='nan'))['candidate_rejection_reason'])
    def test_inverted_bounds(self):
        self.assertIn('inverted',audit(fixture(bad_instance='reversed'))['candidate_rejection_reason'])
    def test_bad_info_index(self):
        self.assertIn('info index',audit(fixture(bad_info=4))['candidate_rejection_reason'])
    def test_missing_info_rejected_not_accepted_as_candidate(self):
        r=audit(fixture(info=False));self.assertEqual(r['candidate_wii_graph_status'],'rejected')
        self.assertIn('info table absent',r['candidate_rejection_reason']);self.assertFalse(r['carbon_pc_abi_proven'])
    def test_missing_aux_rejects(self):
        self.assertIn('aux32',audit(fixture(aux=False))['candidate_rejection_reason'])
    def test_missing_tree_rejects(self):
        self.assertIn('tree',audit(fixture(tree=False))['candidate_rejection_reason'])
    def test_missing_precull_rejects(self):
        self.assertIn('preculler',audit(fixture(prec=False))['candidate_rejection_reason'])
    def test_unaligned_instance_row_rejects(self):
        self.assertIn('not aligned',audit(fixture(extra=b'\x00'))['candidate_rejection_reason'])
    def test_root_padding_residues(self):
        for l in (68,72,76,80):
            with self.subTest(length=l):
                r=audit(fixture(scene_len=l));self.assertEqual(r['candidate_wii_graph_status'],'candidate_internally_consistent')
                self.assertEqual(r['candidate_instance_alignment_padding'],(-8-(8+l)-8)&15)
    def test_big_endian_synthetic_not_proof(self):
        r=audit(fixture(endian='big'),'big');self.assertEqual(r['candidate_wii_graph_status'],'candidate_internally_consistent')
        self.assertFalse(r['carbon_pc_abi_proven'])
    def test_nonfinite_aabb_tolerance_rejected(self):
        with self.assertRaises(v56.CandidateError):v56.candidate_tree(v55.children(fixture(),'little'),[], 'little',float('nan'))
    def test_negative_aabb_tolerance_rejected(self):
        with self.assertRaises(v56.CandidateError):v56.candidate_tree(v55.children(fixture(),'little'),[], 'little',-1.)
    def test_preculler_reference_index_negative(self):
        self.assertIn('preculler',audit(fixture(bad_prec=-1))['candidate_rejection_reason'])
    def test_not_all_precull_blocks_must_be_referenced(self):
        r=audit(fixture(blocks=6));self.assertEqual(r['candidate_wii_graph_status'],'candidate_internally_consistent')
        self.assertEqual(r['candidate_precull']['unreferenced_blocks'],3)
    def test_distinct_synthetic_not_authenticated(self):
        with tempfile.TemporaryDirectory() as tmp:
            srcs=[]
            for i,b in enumerate((fixture(),fixture(n=2))):
                path=Path(tmp)/f'fake{i}.chunk';path.write_bytes(b)
                srcs.append({'label':f'fake{i}','path':str(path),'endian':'little',
                            'expected_file_sha256':v55.sha256(b),'expected_root_sha256':v55.sha256(b)})
            x=v56.survey(srcs)
        self.assertEqual(x['distinct_root_fingerprints'],2)
        self.assertEqual(x['known_authenticated_original_Wii_scenes'],0)
        self.assertFalse(x['new_independent_original_scenes_authenticated'])
    def test_duplicate_synthetic_roots_not_independent(self):
        with tempfile.TemporaryDirectory() as tmp:
            b=fixture();path=Path(tmp)/'same.chunk';path.write_bytes(b)
            spec={'label':'first','path':str(path),'endian':'little',
                  'expected_file_sha256':v55.sha256(b),'expected_root_sha256':v55.sha256(b)}
            x=v56.survey([spec,{**spec,'label':'second'}])
        self.assertEqual(x['submitted_roots'],2);self.assertEqual(x['distinct_root_fingerprints'],1)
    def test_cli_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp);x=d/'root';b=fixture();x.write_bytes(b)
            m=d/'m.json';m.write_text(json.dumps([{'label':'s','path':str(x),'endian':'little',
                'expected_file_sha256':v55.sha256(b),'expected_root_sha256':v55.sha256(b)}]))
            cmd=[sys.executable,str(Path(v56.__file__)),'--manifest',str(m),'--report',str(x)]
            r=subprocess.run(cmd,capture_output=True,text=True)
            self.assertNotEqual(r.returncode,0);self.assertEqual(x.read_bytes(),b)
    def test_cli_report_without_input_bytes_or_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp);x=d/'secret-original-game-root';b=fixture();x.write_bytes(b)
            m=d/'manifest.json';m.write_text(json.dumps([{'label':'synthetic','path':str(x),'endian':'little',
                'expected_file_sha256':v55.sha256(b),'expected_root_sha256':v55.sha256(b)}]))
            out=d/'summary.json';cmd=[sys.executable,str(Path(v56.__file__)),'--manifest',str(m),'--report',str(out)]
            r=subprocess.run(cmd,capture_output=True,text=True)
            self.assertEqual(r.returncode,0,msg=r.stderr)
            y=out.read_text();self.assertNotIn('secret-original-game-root',y)
            self.assertFalse(json.loads(y)['safe_to_install'])


    def test_very_deep_candidate_tree_no_python_recursion_limit(self):
        # >1,000 parent links used to raise RecursionError in V56.
        raw=replace_tree_payload(fixture(n=1),chain_tree(1500))
        result=audit(raw)
        self.assertEqual(result['candidate_wii_graph_status'],'candidate_internally_consistent')
        self.assertEqual(result['candidate_tree']['candidate_48_nodes'],1500)
        self.assertEqual(result['candidate_tree']['covered_instances_exactly_once'],1)
        self.assertEqual(result['candidate_tree']['max_absolute_aabb_union_error'],0.)

    def test_deep_candidate_cycle_rejected_without_recursion(self):
        tree=bytearray(chain_tree(1200))
        # Last node points back to its own index; cannot recurse forever.
        struct.pack_into('<h',tree,(1200-1)*48+28,-(1200-1))
        raw=replace_tree_payload(fixture(n=1),bytes(tree))
        result=audit(raw)
        self.assertEqual(result['candidate_wii_graph_status'],'rejected')
        self.assertIn('cycle',result['candidate_rejection_reason'])

    def test_branch_shares_leaf_rejected(self):
        # Three nodes: root -> children 1 and 2; both reference leaf 0.
        tree=bytearray(chain_tree(3))
        struct.pack_into('<H',tree,12,2)
        struct.pack_into('<h',tree,28,-1)
        struct.pack_into('<h',tree,30,-2)
        struct.pack_into('<h',tree,48+28,0)
        struct.pack_into('<h',tree,96+28,0)
        raw=replace_tree_payload(fixture(n=1),bytes(tree))
        result=audit(raw)
        self.assertEqual(result['candidate_wii_graph_status'],'rejected')
        self.assertIn('multiple times',result['candidate_rejection_reason'])

    def test_unreachable_candidate_node_rejected(self):
        tree=bytearray(chain_tree(2))
        struct.pack_into('<h',tree,28,0)
        raw=replace_tree_payload(fixture(n=1),bytes(tree))
        result=audit(raw)
        self.assertIn('unreachable',result['candidate_rejection_reason'])

    def test_out_of_range_child_rejected(self):
        raw=replace_tree_payload(fixture(n=1),chain_tree(2,root_child_override=-9))
        result=audit(raw)
        self.assertIn('out-of-range',result['candidate_rejection_reason'])

    def test_branching_tree_consistent_bounds(self):
        # Three nodes and two source instances with the same synthetic bounds.
        tree=bytearray(chain_tree(3))
        struct.pack_into('<H',tree,12,2)
        struct.pack_into('<h',tree,28,-1)
        struct.pack_into('<h',tree,30,-2)
        struct.pack_into('<h',tree,48+28,0)
        struct.pack_into('<h',tree,96+28,1)
        result=audit(replace_tree_payload(fixture(n=2),bytes(tree)))
        self.assertEqual(result['candidate_wii_graph_status'],'candidate_internally_consistent')
        self.assertEqual(result['candidate_tree']['covered_instances_exactly_once'],2)


class PrivateWii(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path=os.environ.get('NFS_UC_WII_SCENE')
        if not path or not Path(path).is_file():raise unittest.SkipTest('Original Wii scene not provided')
        cls.src=Path(path).read_bytes()
        if hashlib.sha256(cls.src).hexdigest()!=v56.WII_SHA:raise unittest.SkipTest('Wii source SHA mismatch')
        cls.root=v55.children(cls.src,'little')
        cls.meta={'label':'original-Wii','root_sha256':v56.WII_SHA,'file_sha256':v56.WII_SHA,
                  'endian':'little','platform_hint_unverified':'wii','stream_offset':None}
        cls.report=v56.audit_one(cls.src,cls.root,cls.meta)
    def test_genuine_root_accepted_candidate(self):
        self.assertEqual(self.report['candidate_wii_graph_status'],'candidate_internally_consistent')
    def test_genuine_structure_counts(self):
        self.assertEqual(self.report['candidate_instance_count'],31)
        self.assertEqual(self.report['candidate_tree']['candidate_48_nodes'],8)
        self.assertEqual(self.report['candidate_precull']['candidate_128_blocks'],24)
        self.assertEqual(self.report['candidate_aux32_count'],31)
    def test_genuine_bounds_exact(self):
        self.assertEqual(self.report['candidate_tree']['max_absolute_aabb_union_error'],0.)
    def test_all_preculler_blocks_referenced(self):
        self.assertEqual(self.report['candidate_precull']['referenced_distinct'],24)
        self.assertEqual(self.report['candidate_precull']['unreferenced_blocks'],0)
    def test_info_count_and_alignment(self):
        self.assertEqual(self.report['candidate_info_count'],13)
        self.assertEqual(self.report['candidate_instance_alignment_padding'],4)
    def test_genuine_both_size_hypotheses_still_ambiguous(self):
        self.assertTrue(all(self.report['candidate_size_hypotheses'].values()))
        self.assertFalse(self.report['carbon_pc_abi_proven'])

if __name__=='__main__':unittest.main()