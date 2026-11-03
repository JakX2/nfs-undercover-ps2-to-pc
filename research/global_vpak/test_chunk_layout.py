"""Synthetic-only tests for chunk boundaries and byte-equality comparisons."""
import struct
import unittest

from chunk_layout import CHUNK_ORDER, compare_chunks, parse_chunks


def chunk(tag, body=b""):
    size = 8 + len(body)
    assert size % 16 == 0
    return tag + struct.pack("<I", size) + body


def synthetic_gameplay(export_count=2):
    text = b"ErtS" + struct.pack("<I", 16) + b"name\x00\x00\x00\x00"
    assert len(text) == 16
    chunks = (
        chunk(b"sreV", b"\x11" * 8)
        + chunk(b"NpeD", b"\x22" * 40)
        + chunk(b"NrtS", b"\x00" * 8)
        + chunk(b"NtaD", b"\x33" * 24)
        + chunk(b"NpxE", struct.pack("<II", export_count, 0) + b"\x44" * (16 * export_count))
        + chunk(b"NrtP", b"\x55" * 24)
    )
    # One 20-byte index entry, index_end=64, 16-byte ErtS at 64,
    # 48-byte zero pad to aux at 128, then six aligned chunks.
    header = bytearray(64)
    struct.pack_into("<4sIII", header, 0, b"VPAK", 1, 64, 3)
    struct.pack_into("<5I", header, 16, 0, len(text), len(chunks), 64, 128)
    return bytes(header) + text + b"\x00" * 48 + chunks


class TestChunks(unittest.TestCase):
    def test_six_chunks_and_export_count(self):
        records = parse_chunks(synthetic_gameplay())
        self.assertEqual(len(records), 1)
        self.assertEqual(tuple(k.encode() for k in records[0]["chunks"]), CHUNK_ORDER)
        self.assertEqual(len(records[0]["chunks"]["NpxE"]), 48)

    def test_comparison_equal(self):
        a = parse_chunks(synthetic_gameplay())
        result = compare_chunks(a, a)
        self.assertEqual(result["identical_chunks_except_version"], 1)
        self.assertEqual(result["identical_string_regions"], 1)
        self.assertTrue(all(v == 1 for v in result["identical_chunk_counts"].values()))

    def test_version_only_difference(self):
        a = parse_chunks(synthetic_gameplay())
        b = bytearray(synthetic_gameplay())
        b[136] ^= 0x01  # 128 + 8: first version payload byte
        result = compare_chunks(a, parse_chunks(b))
        self.assertEqual(result["identical_chunks_except_version"], 1)
        self.assertEqual(result["identical_chunk_counts"]["sreV"], 0)

    def test_bad_vpak_magic(self):
        with self.assertRaisesRegex(ValueError, "VPAK"):
            parse_chunks(b"FAKE" + synthetic_gameplay()[4:])

    def test_bad_index_bounds(self):
        b = bytearray(synthetic_gameplay())
        struct.pack_into("<I", b, 8, 16)
        with self.assertRaisesRegex(ValueError, "index bounds"):
            parse_chunks(b)

    def test_record_overlap(self):
        b = bytearray(synthetic_gameplay())
        struct.pack_into("<I", b, 28, 140)  # text_offset after aux_offset
        with self.assertRaisesRegex(ValueError, "Overlapping"):
            parse_chunks(b)

    def test_bad_string_region(self):
        b = bytearray(synthetic_gameplay())
        b[64:68] = b"FAKE"
        with self.assertRaisesRegex(ValueError, "ErtS"):
            parse_chunks(b)

    def test_bad_chunk_tag(self):
        b = bytearray(synthetic_gameplay())
        b[128:132] = b"FAKE"
        with self.assertRaisesRegex(ValueError, "tag"):
            parse_chunks(b)

    def test_oversized_chunk(self):
        b = bytearray(synthetic_gameplay())
        struct.pack_into("<I", b, 132, 0xFFFF_FFF0)
        with self.assertRaisesRegex(ValueError, "chunk size"):
            parse_chunks(b)

    def test_mismatched_export_count(self):
        b = bytearray(synthetic_gameplay())
        npxe_offset = 128 + 16 + 48 + 16 + 32
        struct.pack_into("<I", b, npxe_offset + 8, 100)
        with self.assertRaisesRegex(ValueError, "count/size mismatch"):
            parse_chunks(b)

    def test_unparsed_trailing_bytes(self):
        b = bytearray(synthetic_gameplay())
        b.extend(b"\x00" * 16)
        struct.pack_into("<I", b, 24, struct.unpack_from("<I", b, 24)[0] + 16)
        with self.assertRaisesRegex(ValueError, "Unparsed"):
            parse_chunks(b)


if __name__ == "__main__":
    unittest.main()
