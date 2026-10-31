"""V27 synthetic tests for generated EA-MT10, no extracted game material."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import ea_mt10_synthetic_silence_v27 as tool
from schl_wrapper_audit_v25 import parse_stream, compare


class SyntheticMT10Fixtures(unittest.TestCase):
    def test_lsb_first_bit_writer(self):
        w = tool.BitsLSB()
        w.put(1, 2)  # low bits = 01
        w.put(5, 3)  # next bits = 101
        self.assertEqual(w.finish(), b"\x15")

    def test_bitwriter_rejects_out_of_range(self):
        w = tool.BitsLSB()
        with self.assertRaises(ValueError):
            w.put(4, 2)

    def test_silence_frame_is_compressed_48_bytes(self):
        compressed = tool.compressed_silence_frame()
        self.assertEqual(len(compressed), 48)
        self.assertEqual(compressed[0], 0)  # no raw PCM overlay
        self.assertNotEqual(compressed, b"\x00" * 48)

    def test_silence_frame_generated_deterministically(self):
        self.assertEqual(
            tool.compressed_silence_frame(),
            tool.compressed_silence_frame(),
        )

    def test_pulse_stream_is_not_silence_stream(self):
        original = tool.compressed_silence_frame()
        changed = tool.compressed_silence_frame(pulse=True)
        self.assertEqual(len(changed), len(original))
        self.assertNotEqual(original, changed)

    def test_two_ea_platform_headers(self):
        a, b = tool.build_pair()
        self.assertEqual(a[:4], b"SCHl")
        self.assertEqual(b[:4], b"SCHl")
        self.assertIn(b"PT\x05\x00", a[:16])
        self.assertIn(b"PT\x00\x00", b[:16])
        self.assertEqual(parse_stream(a)["header_size"], 36)
        self.assertEqual(parse_stream(b)["header_size"], 32)

    def test_same_compressed_chunks_across_platforms(self):
        a, b = tool.build_pair()
        with tempfile.TemporaryDirectory() as root:
            left = Path(root) / "ps2.asf"
            right = Path(root) / "pc.asf"
            left.write_bytes(a)
            right.write_bytes(b)
            record = compare(left, right)
        self.assertTrue(record["structurally_lossless_wrapper"])
        self.assertEqual(record["original"]["audio_block_count"], 1)
        self.assertEqual(record["original"]["total_scdl_samples"], 432)

    def test_pulse_audio_blocks_match_across_platforms(self):
        a, b = tool.build_pair(pulse=True)
        with tempfile.TemporaryDirectory() as root:
            left = Path(root) / "ps2.asf"
            right = Path(root) / "pc.asf"
            left.write_bytes(a)
            right.write_bytes(b)
            record = compare(left, right)
        self.assertTrue(record["checks"]["identical_audio_blocks"])
        self.assertTrue(record["checks"]["unchanged_post_header_bytes"])

    def test_actual_codecid_is_ea_mt10(self):
        self.assertEqual(tool.EA_MT10, 4)
        self.assertNotEqual(tool.EA_MT10, 0)  # PCM16 from V26 was codec2 0
        self.assertEqual(tool.SAMPLES, 432)
        self.assertEqual(tool.RATE, 22050)

    def test_invalid_synthetic_platform_rejected(self):
        with self.assertRaises(ValueError):
            tool.make_mt10_header(platform=0, version=3)

    def test_synthetic_fixture_never_embeds_game_audio(self):
        a, b = tool.build_pair()
        self.assertLess(len(a), 256)
        self.assertLess(len(b), 256)
        self.assertEqual(len(a), 121)
        self.assertEqual(len(b), 117)

    def test_pulse_fixture_is_a_different_compressed_bitstream(self):
        a, b = tool.build_pair()
        x, y = tool.build_pair(pulse=True)
        self.assertNotEqual(a, x)
        self.assertNotEqual(b, y)
        self.assertEqual(len(a), len(x))
        self.assertEqual(len(b), len(y))


if __name__ == "__main__":
    unittest.main()
