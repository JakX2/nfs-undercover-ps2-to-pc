"""V26 isolated synthetic tests; no commercial game material or real MT10."""
import hashlib
import struct
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import ea_schl_platform_pcm_selftest_v26 as tool
from schl_wrapper_audit_v25 import compare, parse_stream


class EASCHLPlatformTests(unittest.TestCase):
    def setUp(self):
        self.pcm = tool.make_pcm()
        self.ps2, self.pc = tool.build_pair(self.pcm)

    def test_generated_pcm_has_4096_frames(self):
        self.assertEqual(len(self.pcm), 4096 * 2)

    def test_generated_pcm_is_deterministic(self):
        self.assertEqual(tool.make_pcm(), self.pcm)

    def test_headers_have_correct_platform_tags(self):
        self.assertEqual(self.ps2[:4], b"SCHl")
        self.assertEqual(self.pc[:4], b"SCHl")
        self.assertIn(b"PT\x05\x00", self.ps2[:40])
        self.assertIn(b"PT\x00\x00", self.pc[:40])

    def test_ps2_header_uses_v3_and_pc_uses_v2(self):
        self.assertEqual(tool.make_header(5, 3, priority_patch=True), self.ps2[:36])
        self.assertEqual(tool.make_header(0, 2, priority_patch=False), self.pc[:32])
        self.assertNotEqual(self.ps2[:36], self.pc[:32])

    def test_two_audio_blocks_equal_sample_totals(self):
        result = parse_stream(self.ps2)
        self.assertEqual(result["audio_block_count"], 2)
        self.assertEqual(result["total_scdl_samples"], 4096)
        self.assertEqual(result["declared_block_count"], 2)

    def test_post_header_bytes_identical(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "a.asf"
            q = Path(tmp) / "b.asf"
            p.write_bytes(self.ps2)
            q.write_bytes(self.pc)
            report = compare(p, q)
            self.assertTrue(report["structurally_lossless_wrapper"])
            self.assertEqual(report["original"]["header_size"], 36)
            self.assertEqual(report["experimental"]["header_size"], 32)

    def test_encoding_is_uncompressed_pcm_not_mt10(self):
        self.assertEqual(tool.CODEC2_S16LE_INT, 0)
        self.assertNotEqual(tool.CODEC2_S16LE_INT, 4)
        self.assertEqual(len(hashlib.sha256(self.pcm).hexdigest()), 64)

    def test_bad_platform_version_pair_rejected(self):
        with self.assertRaises(ValueError):
            tool.make_header(0, 3, priority_patch=False)

    def test_patch_value_bounds_checked(self):
        with self.assertRaises(ValueError):
            tool.patch(0x100, 1)
        with self.assertRaises(ValueError):
            tool.patch(0x80, -1)
        with self.assertRaises(ValueError):
            tool.patch(0x80, 1 << 40)

    def test_block_size_rejected_when_pcm_short(self):
        with self.assertRaises(ValueError):
            tool.make_blocks(self.pcm[:-2])

    def test_chunk_types_are_ea_schl_family(self):
        self.assertEqual(self.ps2[:4], b"SCHl")
        expected = ("SCHl", "SCCl", "SCDl", "SCDl", "SCEl")
        self.assertEqual(tuple(parse_stream(self.ps2)["chunk_tags"]), expected)

    def test_two_blocks_have_exact_raw_pcm_bytes(self):
        stream = self.pc
        pos = struct.unpack_from("<I", stream, 4)
        self.assertEqual(stream[pos:pos + 4], b"SCCl")
        pos += struct.unpack_from("<I", stream, pos + 4)[0]
        data = bytearray()
        for _ in range(2):
            self.assertEqual(stream[pos:pos+4], b"SCDl")
            n = struct.unpack_from("<I", stream, pos + 8)[0]
            self.assertEqual(n, 2048)
            start = pos + 16
            data += stream[start:start+n*2]
            pos += struct.unpack_from("<I", stream, pos + 4)[0]
        self.assertEqual(bytes(data), self.pcm)


if __name__ == "__main__":
    unittest.main()
