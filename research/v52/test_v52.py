"""V52 public synthetic and optional private original Wii fixture tests."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import struct
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parent))
import v52_preculler_bit_audit as v52
v50=v52.v50


def instance(index=1, pos=(1.0,2.0,3.0)):
    b=bytearray(96)
    struct.pack_into('<3f',b,0,-1.,-1.,-1.)
    struct.pack_into('<3f',b,16,1.,1.,1.)
    struct.pack_into('<h',b,28,index)
    struct.pack_into('<3f',b,32,*pos)
    return bytes(b)


def mask(b=0x03, footer=(384,384)):
    q=bytearray(128)
    q[1]=b
    struct.pack_into('<2I',q,120,*footer)
    return bytes(q)


def scene(indices=(1,),block_count=2,flags=(0x03,),tail=None,extra_padding=0):
    parts=[(v50.SCENE,b'\0'*68)]
    data=b''.join(struct.pack('<II',tag,len(payload))+payload for tag,payload in parts)
    current=8+len(data)+8
    pad=(-current)&15
    rows=b'\x11'*pad+b''.join(instance(i,(float(j+1),2.,3.)) for j,i in enumerate(indices))
    blocks=[b'\0'*128]
    blocks.extend(mask(flags[(j-1)%len(flags)]) for j in range(1,block_count))
    if tail is not None:blocks[-1]=tail
    parts += [(v50.INSTANCE,rows+extra_padding*b'\0'),(v50.AUX,b'\0'*(32*len(indices))),
              (v50.PRECULLER,b''.join(blocks))]
    body=b''.join(struct.pack('<II',tag,len(payload))+payload for tag,payload in parts)
    return struct.pack('<II',v50.ROOT,len(body))+body


class PublicTests(unittest.TestCase):
    def test_bit_lsb_convention(self):
        self.assertEqual(v52.bits_lsb_first(b'\x81\x01'),{0,7,8})

    def test_no_bits(self):
        self.assertEqual(v52.bits_lsb_first(b'\0'*6),set())

    def test_jaccard_identical(self):
        self.assertEqual(v52.similarity({1,2},{1,2}),1)

    def test_jaccard_disjoint(self):
        self.assertEqual(v52.similarity({1,2},{3}),0)

    def test_jaccard_empty(self):
        self.assertEqual(v52.similarity(set(),set()),1)

    def test_two_blocks_one_instance(self):
        r=v52.audit(scene())
        self.assertEqual((r['instance_count_candidate_96'],r['preculler_block_count_candidate_128']),(1,2))
        self.assertEqual(r['candidate_leading_68B_bits']['union_set_bit_count'],2)

    def test_one_populated_mask_unique(self):
        r=v52.audit(scene())
        self.assertEqual(r['populated_block_unique_candidate_mask_count'],1)

    def test_two_populated_masks_intersection(self):
        r=v52.audit(scene(indices=(1,2),block_count=3,flags=(0x03,0x06)))
        m=r['candidate_leading_68B_bits']
        self.assertEqual((m['intersection_set_bit_count'],m['union_set_bit_count'],m['varying_set_bit_count']),(1,3,2))

    def test_empty_block_may_be_referenced(self):
        r=v52.audit(scene(indices=(0,1)))
        self.assertEqual(r['preculler_index_histogram']['0'],1)
        self.assertEqual(r['empty_block_indices'],[0])

    def test_nonnegative_overflow_reported(self):
        r=v52.audit(scene(indices=(3,),block_count=2))
        self.assertEqual(r['invalid_nonnegative_preculler_indices'],[3])
        self.assertFalse(r['all_nonnegative_indices_in_candidate_range'])

    def test_negative_index_reported(self):
        r=v52.audit(scene(indices=(-1,1)))
        self.assertEqual(r['negative_instance_index_histogram'],{'-1':1})

    def test_mask_frequencies(self):
        r=v52.audit(scene(indices=(1,2),block_count=3,flags=(0x03,0x06)))
        self.assertEqual(r['candidate_leading_68B_bits']['bit_frequency_histogram'],{'1':2,'2':1})

    def test_footer_histogram(self):
        r=v52.audit(scene())
        self.assertEqual(r['footer_u32_pair_histogram'],{'(0, 0)':1,'(384, 384)':1})

    def test_middle_nonzero_does_not_claim_pass(self):
        bad=bytearray(mask())
        bad[80]=0x42
        r=v52.audit(scene(tail=bytes(bad)))
        self.assertFalse(r['bytes_68_to_119_zero_for_all_populated'])
        self.assertFalse(r['pinned_wii_fixture_pattern_match'])

    def test_lowbyte_nonzero_is_reported(self):
        bad=bytearray(mask())
        bad[4]=0x55
        r=v52.audit(scene(tail=bytes(bad)))
        self.assertFalse(r['leading_17_u32_low_byte_zero_for_all_populated'])

    def test_provenance_not_assumed(self):
        r=v52.audit(scene())
        self.assertEqual(r['source_provenance'],'unknown_root')
        self.assertFalse(r['carbon_pc_serialized_schema_verified'])
        self.assertFalse(r['pc_runtime_or_visibility_semantics_verified'])
        self.assertFalse(r['safe_to_install'])

    def test_sha_guard_accept(self):
        b=scene()
        self.assertTrue(v52.audit(b,hashlib.sha256(b).hexdigest())['expected_sha256_guarded'])

    def test_sha_guard_reject(self):
        with self.assertRaises(v50.EvidenceError):
            v52.audit(scene(),'0'*64)

    def test_bad_root_reject(self):
        with self.assertRaises(v50.EvidenceError):
            v52.audit(b'bad')

    def test_incomplete_instance_reject(self):
        with self.assertRaises(v50.EvidenceError):
            v52.audit(scene(extra_padding=1))

    def test_no_candidate_block_reject(self):
        b=scene()
        # Replace payload by empty array while preserving child frame.
        ch=v50.children_of(b)
        p=ch[v50.PRECULLER][0]
        assert p+256==len(b)
        body=bytearray(b[:p]);struct.pack_into('<I',body,p-4,0)
        struct.pack_into('<I',body,4,len(body)-8)
        with self.assertRaises(v50.EvidenceError):
            v52.audit(bytes(body))

    def test_cli_no_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            input_path=Path(d)/'input.chunk';out=Path(d)/'out.json'
            input_path.write_bytes(scene())
            from unittest.mock import patch
            with patch.object(sys,'argv',['prog','--scene',str(input_path),'--report',str(out)]):
                v52.main()
            self.assertTrue(out.exists())
            with patch.object(sys,'argv',['prog','--scene',str(input_path),'--report',str(out)]):
                with self.assertRaises(SystemExit):v52.main()
            self.assertFalse(v52.audit(scene())['safe_to_install'])

    def test_far_apart_never_proves_visibility(self):
        r=v52.audit(scene(indices=(1,2),block_count=3,flags=(0x03,0x07)))
        self.assertIsNotNone(r['illustrative_pair_not_semantic_proof']['spatially_closest'])
        self.assertFalse(r['pc_runtime_or_visibility_semantics_verified'])


class OriginalWiiFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p=os.getenv('NFS_UC_WII_SCENE')
        if not p or not Path(p).is_file():
            raise unittest.SkipTest('Original private Wii fixture not available')
        cls.b=Path(p).read_bytes()
        if hashlib.sha256(cls.b).hexdigest()!=v52.KNOWN_WII_SHA:
            raise unittest.SkipTest('Original private Wii fixture does not match pinned SHA')
        cls.result=v52.audit(cls.b,expected_sha256=v52.KNOWN_WII_SHA)

    def test_31_instances_24_preculler_blocks(self):
        self.assertEqual((self.result['instance_count_candidate_96'],self.result['preculler_block_count_candidate_128']),(31,24))

    def test_wii_observed_candidate_pattern(self):
        self.assertTrue(self.result['pinned_wii_fixture_pattern_match'])

    def test_first_128_block_zero(self):
        self.assertEqual(self.result['empty_block_indices'],[0])

    def test_17_shared_mask_bits_92_union_bits(self):
        b=self.result['candidate_leading_68B_bits']
        self.assertEqual((b['intersection_set_bit_count'],b['union_set_bit_count'],b['varying_set_bit_count']),(17,92,75))

    def test_redbuilding_preculler_20_reference(self):
        self.assertEqual(self.result['preculler_index_histogram']['20'],1)
        self.assertEqual(self.result['preculler_block_count_candidate_128'],24)

    def test_no_carbon_proof(self):
        self.assertFalse(self.result['carbon_pc_serialized_schema_verified'])
        self.assertFalse(self.result['safe_to_install'])


if __name__=='__main__':unittest.main()