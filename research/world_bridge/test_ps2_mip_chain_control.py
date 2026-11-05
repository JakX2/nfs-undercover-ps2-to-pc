"""Synthetic-only mip chain bounds, flag behavior and cross-LOD controls."""
import unittest
from ps2_mip_chain_control import split_mip_chain,decode_mip_chain,analyze_undercover_mip_sections
from test_undercover_texture_variant_visual_control import source_pack


class MipChainTests(unittest.TestCase):
    def test_exact_8bit_three_levels(self):
        raw=bytes(range(64))+bytes(range(16))+bytes(range(4))
        mips=split_mip_chain(raw,8,8,8,3)
        self.assertEqual([(w,h,len(d)) for w,h,d in mips],[(8,8,64),(4,4,16),(2,2,4)])
        self.assertEqual(b''.join(d for _,_,d in mips),raw)

    def test_exact_4bit_levels(self):
        mips=split_mip_chain(bytes(32+8+2),8,8,4,3)
        self.assertEqual([(w,h,len(d)) for w,h,d in mips],[(8,8,32),(4,4,8),(2,2,2)])

    def test_exact_length_rejects_truncated_and_extra(self):
        for data in (bytes(63),bytes(65)):
            with self.subTest(data_len=len(data)),self.assertRaisesRegex(ValueError,'length'):
                split_mip_chain(data,8,8,8,1)

    def test_too_many_levels_rejected(self):
        with self.assertRaisesRegex(ValueError,'dimensions'):
            split_mip_chain(bytes(50),4,4,8,5)

    def test_non_power_of_two_dimensions_rejected(self):
        with self.assertRaisesRegex(ValueError,'dimensions'):
            split_mip_chain(bytes(48),6,8,8,1)

    def test_wrong_depth_rejected(self):
        with self.assertRaisesRegex(ValueError,'dimensions'):
            split_mip_chain(bytes(8),8,8,16,1)

    def test_nonbytes_rejected(self):
        with self.assertRaisesRegex(ValueError,'bytes-like'):
            split_mip_chain([1]*64,8,8,8,1)

    def test_decodes_8bit_linear_mip_chain(self):
        meta={'width':8,'height':8,'codec':8,'mip_levels':2}
        result=decode_mip_chain(bytes(range(64))+bytes(range(16)),meta,0)
        self.assertEqual([(w,h,len(idx)) for w,h,idx in result],[(8,8,64),(4,4,16)])

    def test_invalid_flag_rejected(self):
        meta={'width':8,'height':8,'codec':8,'mip_levels':1}
        with self.assertRaisesRegex(ValueError,'flag'):
            decode_mip_chain(bytes(64),meta,4)

    def test_decode_swizzled_small_level_fails_closed(self):
        meta={'width':8,'height':8,'codec':4,'mip_levels':1}
        with self.assertRaises(ValueError):
            decode_mip_chain(bytes(32),meta,1)

    def test_two_multilevel_synthetic_variants_match_shifted_levels(self):
        sections={241:source_pack(width=16,bits=8,mip_levels=3),3401:source_pack(width=8,bits=8,mip_levels=2)}
        r=analyze_undercover_mip_sections(sections)
        self.assertEqual(r['total_source_texture_records'],4)
        self.assertEqual(r['total_decoded_mip_buffers'],10)
        self.assertEqual(r['total_non_base_mip_buffers'],6)
        self.assertEqual(r['same_size_cross_variant_mip_pairs'],4)
        self.assertEqual(r['mean_rgb_mae_same_size_mips'],0)
        self.assertEqual(r['mean_alpha_mae_same_size_mips'],0)

    def test_bad_source_id_sets_rejected(self):
        with self.assertRaisesRegex(ValueError,'sets disagree'):
            analyze_undercover_mip_sections({241:source_pack(),3401:source_pack(8,hashes=(3,4))})

    def test_missing_original_section_rejected(self):
        with self.assertRaisesRegex(ValueError,'both original'):
            analyze_undercover_mip_sections({241:source_pack()})

    def test_no_asset_identifiers_returned(self):
        r=analyze_undercover_mip_sections({241:source_pack(),3401:source_pack(8)})
        self.assertNotIn('TEST_',repr(r))
        self.assertNotIn('286331153',repr(r))
        self.assertIn('CONSISTENCY ONLY',r['verdict'])


if __name__ == '__main__':unittest.main()
