"""Synthetic-only NrtP section table tests."""
import struct
import unittest

from pointer_sections import parse_pointer_sections, inspect_pointer_sections


def nrtp(rows=None):
    if rows is None:
        rows = [(0, 0x10002, 0), (24, 0x10003, 8),
                (0, 2, 0), (28, 0x10003, 44)]
    body = b''.join(struct.pack('<3I', *row) for row in rows) + b'\0' * 12
    block = b'NrtP' + struct.pack('<I', 0) + body
    block += b'\0' * (-len(block) % 16)
    return block[:4] + struct.pack('<I', len(block)) + block[8:]


class PointerSectionsTests(unittest.TestCase):
    def test_valid_two_sections(self):
        a, b = parse_pointer_sections(nrtp(), 40)
        self.assertEqual(len(a), 1)
        self.assertEqual(len(b), 1)
        self.assertEqual(a[0][2], 8)

    def test_bad_tag(self):
        with self.assertRaisesRegex(ValueError, 'NrtP'):
            parse_pointer_sections(b'WRNG' + nrtp()[4:], 40)

    def test_bad_size(self):
        d = bytearray(nrtp())
        struct.pack_into('<I', d, 4, 999)
        with self.assertRaisesRegex(ValueError, 'size'):
            parse_pointer_sections(bytes(d), 40)

    def test_initial_marker_required(self):
        rows = [(0, 2, 0), (24, 0x10003, 8)]
        with self.assertRaisesRegex(ValueError, 'initial'):
            parse_pointer_sections(nrtp(rows), 40)

    def test_second_marker_required(self):
        rows = [(0, 0x10002, 0), (24, 0x10003, 8)]
        with self.assertRaisesRegex(ValueError, 'second'):
            parse_pointer_sections(nrtp(rows), 40)

    def test_second_marker_duplicate(self):
        rows = [(0, 0x10002, 0), (0, 2, 0), (0, 2, 0)]
        with self.assertRaisesRegex(ValueError, 'second'):
            parse_pointer_sections(nrtp(rows), 40)

    def test_first_region_out_of_bounds(self):
        with self.assertRaisesRegex(ValueError, 'outside text'):
            parse_pointer_sections(nrtp(), 8)

    def test_first_region_one_past_boundary(self):
        with self.assertRaisesRegex(ValueError, 'outside text'):
            parse_pointer_sections(nrtp(), 8)

    def test_bad_kind(self):
        rows = [(0, 0x10002, 0), (24, 9, 8), (0, 2, 0)]
        with self.assertRaisesRegex(ValueError, 'kind'):
            parse_pointer_sections(nrtp(rows), 40)

    def test_bad_source_alignment(self):
        rows = [(0, 0x10002, 0), (25, 0x10003, 8), (0, 2, 0)]
        with self.assertRaisesRegex(ValueError, 'alignment'):
            parse_pointer_sections(nrtp(rows), 40)

    def test_nonzero_padding(self):
        b = bytearray(nrtp())
        b[-1] = 1
        with self.assertRaisesRegex(ValueError, 'padding'):
            parse_pointer_sections(bytes(b), 40)

    def test_zero_sentinel_missing(self):
        b = bytearray(nrtp())
        for i in range(len(b) - 16, len(b), 4):
            struct.pack_into('<I', b, i, 0x1234)
        with self.assertRaises(ValueError):
            parse_pointer_sections(bytes(b), 40)

    def test_empty_sections_supported(self):
        a, b = parse_pointer_sections(nrtp([(0, 0x10002, 0), (0, 2, 0)]), 0)
        self.assertEqual((a, b), ([], []))

    def test_inspect_summary(self):
        r = {'text': b'ErtS' + struct.pack('<I', 16) + b'x\0' * 4,
             'chunks': {'NrtP': nrtp(), 'NtaD': b'NtaD' + b'\0' * 28}}
        result = inspect_pointer_sections([r])
        self.assertEqual(result['initial_marker_count'], 1)
        self.assertEqual(result['first_section_entries'], 1)
        self.assertEqual(result['second_section_targets_beyond_ntad'], 1)


if __name__ == '__main__':
    unittest.main()
