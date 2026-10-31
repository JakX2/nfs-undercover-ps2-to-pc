"""V30 synthetic regression coverage: multiple EA-MT10 frames in ONE SCDl."""
import struct
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import ea_mt10_multiframe_scdl_v30 as v30
from ea_mt10_multiblock_continuity_v29 import (
    FRAME_PATTERN, FRAME_SAMPLES, MultiBlockError, make_ps2_stream, synth_frame,
)
from schl_wrapper_audit_v25 import compare, parse_stream
from undercover_mt10_private_bridge_v28 import convert, parse_header


class MicrotalkSingleBlockTests(unittest.TestCase):
    def setUp(self):
        self.raw = v30.make_single_block_stream()
        self.old = make_ps2_stream()

    def test_one_data_block_for_three_frames(self):
        result = parse_stream(self.raw)
        self.assertEqual(result["audio_block_count"], 1)
        self.assertEqual(result["declared_block_count"], 1)
        self.assertEqual(result["chunk_tags"], ["SCHl", "SCCl", "SCDl", "SCEl"])

    def test_exact_total_samples(self):
        result = parse_stream(self.raw)
        self.assertEqual(result["total_scdl_samples"], 1296)
        self.assertEqual(result["total_scdl_samples"], parse_stream(self.old)["total_scdl_samples"])

    def test_ps2_header_is_unchanged_from_v29(self):
        size = struct.unpack_from("<I", self.raw, 4)[0]
        self.assertEqual(self.raw[:size], self.old[:size])

    def test_header_is_ps2_mono_mt10(self):
        h = parse_header(self.raw)
        self.assertEqual((h["platform"], h["version"], h["channels"], h["codec2"]),
                         (5, 3, 1, 4))
        self.assertEqual((h["sample_count"], h["rate"]), (1296, 22050))

    def test_all_three_frames_present_in_single_data_payload(self):
        p = struct.unpack_from("<I", self.raw, 4)[0] + 12
        self.assertEqual(self.raw[p:p+4], b"SCDl")
        self.assertEqual(struct.unpack_from("<I", self.raw, p+8)[0], 1296)
        payload = self.raw[p+17:p+struct.unpack_from("<I", self.raw, p+4)[0]]
        expected = b"".join(
            synth_frame(first=i == 0, pulse=active)
            for i, active in enumerate(FRAME_PATTERN)
        )
        self.assertEqual(payload, expected)

    def test_only_initial_frame_has_codec_initializer(self):
        a = synth_frame(first=True, pulse=False)
        b = synth_frame(first=False, pulse=True)
        self.assertEqual(len(a), 48)
        self.assertEqual(len(b), 47)  # extra RELP excitation bit expands this frame
        self.assertEqual(len(self.raw), len(self.old) - 2 * 17 + 0)

    def test_rewrap_preserves_original_post_header(self):
        pc, metadata = convert(self.raw)
        ah = parse_header(self.raw)["header_size"]
        bh = parse_header(pc)["header_size"]
        self.assertEqual(self.raw[ah:], pc[bh:])
        self.assertEqual(metadata["scdl_blocks"], 1)

    def test_target_header_is_pc_v2_microtalk(self):
        pc, _ = convert(self.raw)
        h = parse_header(pc)
        self.assertEqual((h["platform"], h["version"], h["codec2"]), (0, 2, 4))
        self.assertEqual((h["sample_count"], h["rate"]), (1296, 22050))

    def test_independent_auditor_accepts_rewrap(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = Path(tmp) / "orig.asf"
            b = Path(tmp) / "pc.asf"
            a.write_bytes(self.raw)
            b.write_bytes(convert(self.raw)[0])
            checks = compare(a, b)
        self.assertTrue(checks["structurally_lossless_wrapper"])
        self.assertTrue(checks["checks"]["unchanged_post_header_bytes"])

    def test_negative_control_changes_the_body(self):
        control = v30.make_single_block_stream((False, False, False))
        with tempfile.TemporaryDirectory() as tmp:
            a = Path(tmp) / "orig.asf"
            b = Path(tmp) / "control.asf"
            a.write_bytes(self.raw)
            b.write_bytes(control)
            checks = compare(a, b)
        self.assertFalse(checks["structurally_lossless_wrapper"])

    def test_deterministic_generated_audio(self):
        self.assertEqual(self.raw, v30.make_single_block_stream())

    def test_two_frames_supported(self):
        raw = v30.make_single_block_stream((False, True))
        self.assertEqual(parse_stream(raw)["total_scdl_samples"], 864)
        self.assertEqual(parse_stream(raw)["audio_block_count"], 1)

    def test_eight_frames_supported(self):
        raw = v30.make_single_block_stream((False, True) * 4)
        self.assertEqual(parse_stream(raw)["total_scdl_samples"], 3456)
        self.assertEqual(parse_stream(raw)["audio_block_count"], 1)

    def test_single_frame_fixture_rejected(self):
        with self.assertRaises(MultiBlockError):
            v30.make_single_block_stream((False,))

    def test_nine_frame_fixture_rejected(self):
        with self.assertRaises(MultiBlockError):
            v30.make_single_block_stream((False,) * 9)

    def test_generated_fixture_is_small_and_not_game_data(self):
        self.assertLess(len(self.raw), 512)
        self.assertIn(b"SCHl", self.raw)
        self.assertIn(b"SCDl", self.raw)


if __name__ == "__main__":
    unittest.main()
