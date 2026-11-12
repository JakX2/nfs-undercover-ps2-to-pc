"""Synthetic-only regression tests for world-section spatial identities."""
import struct
import unittest
from section_identity_anchor import (ROW_SIZE, parse_rows, compare_rows,
                                     classify_marker, sample_markers, summarize)


def row(name=b'A1', section=101, offset=0, size=4096,
        centre=(1.25, -5.75), radius=25.0, priority=200, checksum=12345):
    out = bytearray(ROW_SIZE)
    out[:len(name)] = name
    struct.pack_into('<h', out, 8, section)
    struct.pack_into('<I', out, 0x10, 1)
    struct.pack_into('<III', out, 0x14, offset, size, size)
    struct.pack_into('<I', out, 0x24, priority)
    struct.pack_into('<3f', out, 0x28, centre[0], centre[1], radius)
    struct.pack_into('<I', out, 0x34, checksum)
    return bytes(out)


class SectionIdentityTests(unittest.TestCase):
    def test_parse_two_rows(self):
        a = parse_rows(row() + row(b'B2', 102, 4096), 8192)
        self.assertEqual(set(a), {101, 102})
        self.assertEqual(summarize(a)['offsets_aligned_2048'], 2)

    def test_reject_stride(self):
        with self.assertRaisesRegex(ValueError, '92-byte'):
            parse_rows(row() + b'x', 8192)

    def test_empty_rejected(self):
        with self.assertRaisesRegex(ValueError, 'nonempty'):
            parse_rows(b'', 10000)

    def test_duplicate_id(self):
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            parse_rows(row() + row(b'B2', 101, 4096), 8192)

    def test_out_of_stream(self):
        with self.assertRaisesRegex(ValueError, 'out-of-bounds'):
            parse_rows(row(offset=4096, size=4096), 4097)

    def test_overlap(self):
        with self.assertRaisesRegex(ValueError, 'Overlapping'):
            parse_rows(row(size=7000) + row(b'B2', 102, 4096), 16000)

    def test_bad_name(self):
        with self.assertRaisesRegex(ValueError, 'name'):
            parse_rows(row(name=b'\xff'), 8192)

    def test_nonfinite_float(self):
        with self.assertRaisesRegex(ValueError, 'Nonfinite'):
            parse_rows(row(centre=(float('nan'), 0)), 8192)

    def test_negative_radius(self):
        with self.assertRaisesRegex(ValueError, 'negative radius'):
            parse_rows(row(radius=-1), 8192)

    def test_matching_spatial_nonzero_despite_packaging(self):
        a = parse_rows(row(offset=0, size=1000), 9000)
        b = parse_rows(row(offset=4096, size=1400), 9000)
        c = compare_rows(a, b)
        self.assertEqual(c['matching_nonzero_spatial_triplets'], 1)
        self.assertEqual(c['matching_stream_offsets'], 0)
        self.assertEqual(c['matching_serialized_sizes'], 0)

    def test_matching_zero_spatial_separate(self):
        a = parse_rows(row(centre=(0.0, 0.0), radius=0), 9000)
        b = parse_rows(row(centre=(0.0, 0.0), radius=0), 9000)
        c = compare_rows(a, b)
        self.assertEqual(c['matching_both_zero_spatial_triplets'], 1)
        self.assertEqual(c['matching_nonzero_spatial_triplets'], 0)

    def test_different_nonzero_spatial_despite_same_name_and_number(self):
        a = parse_rows(row(), 9000)
        b = parse_rows(row(centre=(99.0, -5.75)), 9000)
        c = compare_rows(a, b)
        self.assertEqual((c['matching_names'], c['different_spatial_triplets']), (1, 1))

    def test_classify_geometry(self):
        self.assertEqual(classify_marker(struct.pack('<II', 0x80134000, 8), 0), 'geometry_pack')

    def test_classify_collision_island(self):
        self.assertEqual(classify_marker(struct.pack('<II', 0x3B802, 8), 0), 'collision_grid_island_data')

    def test_classify_texture(self):
        self.assertEqual(classify_marker(struct.pack('<II', 0xB3300000, 8), 0), 'texture_pack')

    def test_classify_framed_geometry(self):
        data = b'\0' * 40 + struct.pack('<II', 0x80134000, 512) + b'\0' * 40
        self.assertEqual(classify_marker(data, 0), 'geometry_pack_after_initial_framing')

    def test_short_prefix_unsampled(self):
        self.assertIsNone(classify_marker(b'\0' * 4, 0))

    def test_unknown_marker_does_not_guess(self):
        self.assertEqual(classify_marker(struct.pack('<II', 0xDEADBEEF, 16), 0), 'other_or_unresolved')

    def test_sample_safeguards_offset(self):
        rows = parse_rows(row(offset=4096, size=100), 9000)
        result = sample_markers(rows, b'\0' * 50)
        self.assertEqual(result['sampled_section_starts'], 0)

    def test_shared_number_set(self):
        a = parse_rows(row(section=10) + row(b'B2', 11, 4096), 9000)
        b = parse_rows(row(section=10) + row(b'C3', 12, 4096), 9000)
        c = compare_rows(a, b)
        self.assertEqual((c['shared_section_numbers'], c['only_left'], c['only_right']), (1, 1, 1))


if __name__ == '__main__':
    unittest.main()
