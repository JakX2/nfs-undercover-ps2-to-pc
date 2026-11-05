"""Synthetic-only alpha interpretation regression tests; no original assets."""
import unittest
from carbon_ps2_alpha_provenance_audit import score_alpha_candidates, compare_source_alpha_sections
from test_texture_visual_pair_gate import make_pack
from test_carbon_ps2_texture_color_control import corrupt_flag


class AlphaSemanticsTests(unittest.TestCase):
    def score(self,pc_alpha,ps2_alpha):
        pc=bytes((30,40,50,pc_alpha))*4
        pal=bytearray(16*4)
        pal[0:4]=bytes((30,40,50,ps2_alpha))
        return score_alpha_candidates(pc,2,2,bytes(4),2,2,bytes(pal),4)

    def test_dxt1_like_opaque_has_exact_opaque_candidate(self):
        r=self.score(255,0)
        self.assertEqual(r['mae']['opaque'],0)
        self.assertEqual(r['mae']['double'],255)
        self.assertEqual(r['pc_nonopaque_pixels'],0)
        self.assertEqual(r['ps2_raw_alpha_zero_pixels'],4)

    def test_ps2_half_range_alpha_doubles(self):
        r=self.score(128,64)
        self.assertEqual(r['mae']['double'],0)
        self.assertEqual(r['mae']['raw'],64)

    def test_ps2_alpha_128_clamps_to_255(self):
        r=self.score(255,128)
        self.assertEqual(r['mae']['double'],0)
        self.assertEqual(r['ps2_raw_alpha_128_pixels'],4)

    def test_binary_nonzero_vs_binary_ge64_not_identical(self):
        r=self.score(255,1)
        self.assertEqual(r['mae']['binary_nonzero'],0)
        self.assertEqual(r['mae']['binary_ge64'],255)

    def test_zero_candidate(self):
        r=self.score(0,128)
        self.assertEqual(r['mae']['zero'],0)
        self.assertEqual(r['pc_nonopaque_pixels'],4)

    def test_nearest_downsample_uses_pixel_centres(self):
        colors=bytearray()
        for y in range(4):
            for x in range(4):
                colors.extend((10,10,10,255 if x>=2 else 0))
        pal=bytearray(16*4)
        pal[0:4]=bytes((10,10,10,0))
        pal[4:8]=bytes((10,10,10,128))
        r=score_alpha_candidates(bytes(colors),4,4,bytes((0,1)),2,1,bytes(pal),4)
        self.assertEqual(r['mae']['double'],0)

    def test_bad_dimensions(self):
        with self.assertRaisesRegex(ValueError,'dimensions'):
            score_alpha_candidates(bytes(4),0,1,bytes(1),1,1,bytes(64),4)

    def test_bad_index_range(self):
        with self.assertRaisesRegex(ValueError,'outside'):
            score_alpha_candidates(bytes(4),1,1,bytes((16,)),1,1,bytes(64),4)

    def test_wrong_pixel_buffer(self):
        with self.assertRaisesRegex(ValueError,'lengths'):
            score_alpha_candidates(bytes(3),1,1,bytes((0,)),1,1,bytes(64),4)

    def test_wrong_palette_buffer(self):
        with self.assertRaisesRegex(ValueError,'lengths'):
            score_alpha_candidates(bytes(4),1,1,bytes((0,)),1,1,bytes(63),4)

    def test_source_alpha_audit_returns_only_aggregates(self):
        r=compare_source_alpha_sections(make_pack(),make_pack('ps2'))
        self.assertEqual(r['matched_texture_count'],2)
        self.assertEqual(r['by_pc_dxt_codec']['DXT1']['textures'],2)
        self.assertEqual(r['by_pc_dxt_codec']['DXT1']['fully_opaque_pc_textures'],2)
        self.assertIn('COMPARISON ONLY',r['verdict'])
        self.assertNotIn('SYNTHETIC_',repr(r))

    def test_bad_source_swizzle_flag_fails_closed(self):
        with self.assertRaisesRegex(ValueError,'flag'):
            compare_source_alpha_sections(make_pack(),corrupt_flag(make_pack('ps2'),2))

    def test_bad_identity_fails_closed(self):
        with self.assertRaisesRegex(ValueError,'identity'):
            compare_source_alpha_sections(make_pack(),make_pack('ps2',name_prefix=b'OTHER_'))

    def test_no_matching_identity_rejected(self):
        with self.assertRaisesRegex(ValueError,'two matched'):
            compare_source_alpha_sections(make_pack(),make_pack('ps2',hashes=(3,4)))


if __name__ == '__main__':unittest.main()
