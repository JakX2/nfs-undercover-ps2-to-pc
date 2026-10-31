"""V29 regression fixtures: independently generated EA MicroTalk blocks only."""
import struct
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import ea_mt10_multiblock_continuity_v29 as v29
from ea_mt10_synthetic_silence_v27 import compressed_silence_frame
from schl_wrapper_audit_v25 import parse_stream, compare
from undercover_mt10_private_bridge_v28 import convert, parse_header


class MultiBlockFixtureTests(unittest.TestCase):
    def test_first_frame_matches_v27_original_silence_encoding(self):
        self.assertEqual(
            v29.synth_frame(first=True, pulse=False),
            compressed_silence_frame(pulse=False)
        )

    def test_first_frame_matches_v27_original_pulse_encoding(self):
        self.assertEqual(
            v29.synth_frame(first=True, pulse=True),
            compressed_silence_frame(pulse=True)
        )

    def test_continuation_frame_has_no_repeated_global_header(self):
        self.assertEqual(len(v29.synth_frame(first=True, pulse=False)), 48)
        self.assertEqual(len(v29.synth_frame(first=False, pulse=False)), 46)
        self.assertNotEqual(
            v29.synth_frame(first=True, pulse=False),
            v29.synth_frame(first=False, pulse=False)
        )

    def test_continuation_frame_has_nonzero_pulse(self):
        a = v29.synth_frame(first=False, pulse=False)
        b = v29.synth_frame(first=False, pulse=True)
        self.assertNotEqual(a, b)
        self.assertGreaterEqual(len(b), len(a))

    def test_three_complete_ea_blocks_and_sample_counts(self):
        raw = v29.make_ps2_stream()
        result = parse_stream(raw)
        self.assertEqual(result["declared_block_count"], 3)
        self.assertEqual(result["audio_block_count"], 3)
        self.assertEqual(result["total_scdl_samples"], 1296)
        self.assertEqual(
            result["chunk_tags"],
            ["SCHl", "SCCl", "SCDl", "SCDl", "SCDl", "SCEl"],
        )

    def test_source_profile_is_ps2_v3_ea_mt10(self):
        header = parse_header(v29.make_ps2_stream())
        self.assertEqual(header["platform"], 5)
        self.assertEqual(header["version"], 3)
        self.assertEqual(header["rate"], 22050)
        self.assertEqual(header["channels"], 1)
        self.assertEqual(header["codec2"], 4)
        self.assertEqual(header["sample_count"], 1296)

    def test_v28_pc_rewrap_preserves_all_postheader_bytes(self):
        a = v29.make_ps2_stream()
        b, metadata = convert(a)
        ah = parse_header(a)["header_size"]
        bh = parse_header(b)["header_size"]
        self.assertEqual(a[ah:], b[bh:])
        self.assertEqual(metadata["target_header"]["platform"], 0)
        self.assertEqual(metadata["target_header"]["version"], 2)
        self.assertEqual(metadata["scdl_blocks"], 3)

    def test_independent_audit_accepts_v28_rewrap(self):
        original = v29.make_ps2_stream()
        converted, _ = convert(original)
        with tempfile.TemporaryDirectory() as tmp:
            a = Path(tmp) / "ps2.asf"
            b = Path(tmp) / "pc.asf"
            a.write_bytes(original)
            b.write_bytes(converted)
            verified = compare(a, b)
        self.assertTrue(verified["structurally_lossless_wrapper"])
        self.assertTrue(verified["checks"]["identical_audio_blocks"])

    def test_altered_middle_pulse_detected_structurally(self):
        original = v29.make_ps2_stream((False, True, False))
        mutated = v29.make_ps2_stream((False, False, False))
        with tempfile.TemporaryDirectory() as tmp:
            a = Path(tmp) / "original.asf"
            b = Path(tmp) / "negative_control.asf"
            a.write_bytes(original)
            b.write_bytes(mutated)
            report = compare(a, b)
        self.assertFalse(report["structurally_lossless_wrapper"])
        self.assertFalse(report["checks"]["identical_audio_blocks"])

    def test_sccl_count_is_three(self):
        raw = v29.make_ps2_stream()
        header_size = struct.unpack_from("<I", raw, 4)[0]
        self.assertEqual(raw[header_size:header_size+4], b"SCCl")
        self.assertEqual(struct.unpack_from("<I", raw, header_size+8)[0], 3)

    def test_first_scdl_contains_first_frame(self):
        raw = v29.make_ps2_stream()
        first = struct.unpack_from("<I", raw, 4)[0] + 12
        self.assertEqual(raw[first:first+4], b"SCDl")
        self.assertEqual(struct.unpack_from("<I", raw, first+8)[0], 432)
        self.assertEqual(
            raw[first+17:first+17+48],
            v29.synth_frame(first=True, pulse=False)
        )

    def test_second_scdl_has_no_global_header(self):
        raw = v29.make_ps2_stream()
        first = struct.unpack_from("<I", raw, 4)[0] + 12
        second = first + struct.unpack_from("<I", raw, first+4)[0]
        self.assertEqual(raw[second:second+4], b"SCDl")
        self.assertEqual(struct.unpack_from("<I", raw, second+8)[0], 432)
        second_payload = v29.synth_frame(first=False, pulse=True)
        self.assertEqual(raw[second+17:second+17+len(second_payload)], second_payload)

    def test_reject_single_block_fixture(self):
        with self.assertRaises(v29.MultiBlockError):
            v29.make_ps2_stream((True,))

    def test_reject_more_than_eight_fixture_blocks(self):
        with self.assertRaises(v29.MultiBlockError):
            v29.make_ps2_stream((False,)*9)

    def test_three_identical_silent_frames_still_have_three_blocks(self):
        raw = v29.make_ps2_stream((False, False, False))
        self.assertEqual(parse_stream(raw)["audio_block_count"], 3)

    def test_no_game_assets_are_needed(self):
        raw = v29.make_ps2_stream()
        self.assertLess(len(raw), 1024)
        self.assertIn(b"SCHl", raw)
        self.assertIn(b"SCDl", raw)


if __name__ == "__main__":
    unittest.main()
