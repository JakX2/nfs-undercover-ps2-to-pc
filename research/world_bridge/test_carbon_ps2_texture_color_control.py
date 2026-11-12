"""Source-free, synthetic Carbon texture RGB control and failure regression."""
import struct
import unittest
from test_texture_visual_pair_gate import make_pack
from carbon_ps2_texture_color_control import compare_source_color_sections


def corrupt_flag(pack, value):
    # Mutate only the first platform +0x17 byte in a source-free fixture.
    data=bytearray(pack)
    needle=struct.pack('<II',0x33310005,168)
    at=data.find(needle)
    assert at >= 0
    data[at+8+0x17]=value
    return bytes(data)


class ColorControlTests(unittest.TestCase):
    def test_linear_8bit_rgb_matches(self):
        report=compare_source_color_sections(make_pack(),make_pack('ps2',bits=8))
        self.assertEqual(report['shared_source_identities'],2)
        self.assertEqual(report['decoded_base_images'],2)
        self.assertEqual(report['ps2_swizzle_flag_counts'],{'0':2})
        self.assertEqual(report['by_indexed_depth']['8']['mean_rgb_mae'],0)
        self.assertGreater(report['texture_pixel_base_padding_bytes']['ps2'],0)
        self.assertIn('UNVERIFIED',report['verdict'])

    def test_linear_4bit_rgb_matches(self):
        report=compare_source_color_sections(make_pack(),make_pack('ps2',bits=4))
        self.assertEqual(report['by_indexed_depth']['4']['mean_rgb_mae'],0)

    def test_unknown_swizzle_flag_rejected(self):
        with self.assertRaisesRegex(ValueError,'swizzle flag'):
            compare_source_color_sections(make_pack(),corrupt_flag(make_pack('ps2'),2))

    def test_swizzle_one_on_8x8_fails_closed(self):
        with self.assertRaisesRegex(ValueError,'addresses bytes|not initialized'):
            compare_source_color_sections(make_pack(),corrupt_flag(make_pack('ps2'),1))

    def test_mismatch_hashes_rejected(self):
        with self.assertRaisesRegex(ValueError,'two matched'):
            compare_source_color_sections(make_pack(),make_pack('ps2',hashes=(3,4)))

    def test_bad_identity_name_rejected(self):
        with self.assertRaisesRegex(ValueError,'metadata disagrees'):
            compare_source_color_sections(make_pack(),make_pack('ps2',name_prefix=b'OTHER_'))

    def test_no_identifiers_leaked_in_aggregate(self):
        report=compare_source_color_sections(make_pack(),make_pack('ps2'))
        self.assertNotIn('SYNTHETIC_',repr(report))
        self.assertNotIn('286331153',repr(report))


if __name__=='__main__':unittest.main()
