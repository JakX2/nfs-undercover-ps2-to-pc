"""Synthetic-only tests for indexed VPAK name-pool alignment."""
import struct
import unittest

from record_alignment import best_cross_index_match, compare_aligned, record_names


def fixture(names):
    payload = b"\0".join(s.encode("ascii") for s in names) + b"\0"
    payload += b"\0" * (-(len(payload) + 8) % 4)
    block = b"ErtS" + struct.pack("<I", len(payload) + 8) + payload
    header = bytearray(64)
    struct.pack_into("<4sIII", header, 0, b"VPAK", 1, 64, 23)
    struct.pack_into("<5I", header, 16, 0, len(block), 0, 64, 64 + len(block))
    return bytes(header) + block


class AlignmentTests(unittest.TestCase):
    def test_editor_marker_removed(self):
        self.assertEqual(
            record_names(fixture(["a", "NFS-VltEd 4.6.0.0 by nfsu360", "b"])),
            [("a", "b")],
        )

    def test_invalid_size_rejected(self):
        buf = bytearray(fixture(["a"]))
        struct.pack_into("<I", buf, 20, 99999)
        with self.assertRaises(ValueError):
            record_names(buf)

    def test_bad_magic_rejected(self):
        with self.assertRaises(ValueError):
            record_names(b"NOTVPAK")

    def test_order_vs_set(self):
        result = compare_aligned([("a", "b"), ("x",)], [("b", "a"), ("y",)])
        self.assertEqual(result["same_index_identical_name_sets"], 1)
        self.assertEqual(result["same_index_identical_ordered_name_lists"], 0)
        self.assertEqual(result["name_set_difference_indices_first_20"], [1])

    def test_cross_index_match(self):
        result = best_cross_index_match([("a", "b"), ("x",)], [("z",), ("a", "b")])
        self.assertEqual(result["highest_jaccard"], 1.0)
        self.assertEqual(result["highest_overlap_left_index"], 0)
        self.assertEqual(result["highest_overlap_right_index"], 1)

    def test_empty_rejected(self):
        with self.assertRaises(ValueError):
            best_cross_index_match([], [("a",)])


if __name__ == "__main__":
    unittest.main()
