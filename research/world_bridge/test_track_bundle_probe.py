"""Synthetic-only tests for track chunk comparison and bounded split reader."""
import struct
import tempfile
import unittest
from pathlib import Path

from track_bundle_probe import (chunk_inventory, compare_inventories,
                                common_prefix_len, prefix_root, SplitZip)


def bundle(*pairs):
    return b''.join(struct.pack('<II', cid, len(data)) + data for cid, data in pairs)


class TrackProbeTests(unittest.TestCase):
    def test_inventory(self):
        parts = chunk_inventory(bundle((0x34110, b'abc'), (0x34112, b'')))
        self.assertEqual([x['id'] for x in parts], ['0x00034110', '0x00034112'])
        self.assertEqual([x['bytes'] for x in parts], [3, 0])

    def test_duplicate_occurrences(self):
        parts = chunk_inventory(bundle((5, b'a'), (5, b'b')))
        self.assertEqual([x['occurrence'] for x in parts], [0, 1])

    def test_empty_bundle(self):
        self.assertEqual(chunk_inventory(b''), [])

    def test_truncated_header(self):
        with self.assertRaisesRegex(ValueError, 'Truncated'):
            chunk_inventory(b'123')

    def test_payload_outside_bundle(self):
        with self.assertRaisesRegex(ValueError, 'out of bounds'):
            chunk_inventory(struct.pack('<II', 123, 999) + b'x')

    def test_equal_nonempty_chunks(self):
        a = chunk_inventory(bundle((0x34110, b'alpha')))
        c = compare_inventories(a, a)
        self.assertEqual((c['same_id_and_occurrence'], c['identical_chunks'],
                          c['identical_nonempty_chunks']), (1, 1, 1))

    def test_same_size_different_bytes(self):
        a = chunk_inventory(bundle((0x34110, b'alpha')))
        b = chunk_inventory(bundle((0x34110, b'bravo')))
        c = compare_inventories(a, b)
        self.assertEqual((c['same_id_and_occurrence'], c['identical_chunks']), (1, 0))

    def test_empty_chunks_do_not_count_nonempty(self):
        a = chunk_inventory(bundle((0x34112, b'')))
        self.assertEqual(compare_inventories(a, a)['identical_nonempty_chunks'], 0)

    def test_common_prefix(self):
        self.assertEqual(common_prefix_len(b'abcdef', b'abcZef'), 3)
        self.assertEqual(common_prefix_len(b'abc', b'abcdef'), 3)

    def test_root_within_128_bytes(self):
        data = bytes(40) + struct.pack('<II', 0x80134000, 16) + bytes(16)
        r = prefix_root(data)
        self.assertTrue(r['root_found_in_first_128_bytes'])
        self.assertEqual(r['root_offset'], 40)
        self.assertEqual(r['root_declared_bytes'], 16)

    def test_marker_outside_initial_scan(self):
        data = bytes(140) + struct.pack('<II', 0x80134000, 8) + bytes(16)
        self.assertFalse(prefix_root(data)['root_found_in_first_128_bytes'])

    def test_split_missing_volume(self):
        with tempfile.TemporaryDirectory() as folder:
            final = Path(folder, 'TRACKS.zip')
            final.write_bytes(b'not a zip')
            with self.assertRaisesRegex(ValueError, 'Provide existing split volumes'):
                SplitZip([Path(folder, 'missing.z01'), final])


if __name__ == '__main__':
    unittest.main()
