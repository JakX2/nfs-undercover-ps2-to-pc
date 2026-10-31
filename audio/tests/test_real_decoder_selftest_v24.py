"""Synthetic V24 regression tests; real CLI integration runs in GitHub Actions."""
import sys
import tempfile
import unittest
import wave
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import vgmstream_real_decoder_selftest_v24 as v24
from vgmstream_metadata_preflight_v23 import ProbeError


class V24FixtureTests(unittest.TestCase):
    def test_generated_pcm_length(self):
        self.assertEqual(len(v24.raw_samples()), v24.FRAMES * 2)

    def test_generated_pcm_is_deterministic(self):
        self.assertEqual(v24.raw_samples(), v24.raw_samples())

    def test_exactly_one_generated_sample_differs_by_one_bit(self):
        a = v24.raw_samples()
        b = v24.raw_samples(changed=True)
        changed = [(i, x, y) for i, (x, y) in enumerate(zip(a, b)) if x != y]
        self.assertEqual(len(changed), 1)
        self.assertEqual(changed[0][1] ^ changed[0][2], 1)

    def test_txth_is_pcm16_not_ea_mt10(self):
        self.assertIn("codec = PCM16LE", v24.TXTH)
        self.assertIn("channels = 1", v24.TXTH)
        self.assertIn("sample_rate = 22050", v24.TXTH)
        self.assertIn("num_samples = 4096", v24.TXTH)
        self.assertNotIn("MT10", v24.TXTH)

    def test_own_generated_samples_fit_signed_16_bit(self):
        values = v24.raw_samples()
        for i in range(0, len(values), 2):
            sample = int.from_bytes(values[i:i+2], "little", signed=True)
            self.assertGreaterEqual(sample, -32768)
            self.assertLessEqual(sample, 32767)

    def test_selftest_rejects_decoder_corrupting_pcm(self):
        def fake_metadata(*args, **kwargs):
            return {"channels": 1, "sample_rate_hz": 22050,
                    "total_samples": 4096, "encoding": "PCM16LE"}

        def bad_decode(_decoder, _src, out):
            with wave.open(str(out), "wb") as w:
                w.setnchannels(1)
                w.setframerate(22050)
                w.setsampwidth(2)
                w.writeframes(b"\x00\x00" * v24.FRAMES)

        with patch.object(v24, "get_metadata", side_effect=fake_metadata):
            with patch.object(v24, "decode", side_effect=bad_decode):
                with self.assertRaises(ProbeError):
                    v24.selftest(Path("/not/a/real/decoder"))

    def test_selftest_has_unambiguous_limitations(self):
        def fake_metadata(*args, **kwargs):
            return {"channels": 1, "sample_rate_hz": 22050,
                    "total_samples": 4096, "encoding": "PCM16LE"}

        def identity_decode(_decoder, src, out):
            with wave.open(str(out), "wb") as w:
                w.setnchannels(1)
                w.setframerate(22050)
                w.setsampwidth(2)
                w.writeframes(src.read_bytes())

        with patch.object(v24, "get_metadata", side_effect=fake_metadata):
            with patch.object(v24, "decode", side_effect=identity_decode):
                report = v24.selftest(Path("/not/a/real/decoder"))
        self.assertTrue(report["pcm_roundtrip_identical"])
        self.assertTrue(report["single_bit_mutation_detected"])
        self.assertFalse(report["actual_ea_mt10_decoded"])
        self.assertFalse(report["carbon_pc_runtime_tested"])


if __name__ == "__main__":
    unittest.main()
