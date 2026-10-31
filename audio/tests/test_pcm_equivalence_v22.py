"""Synthetic regression tests only. These do not prove EA-MT10 decoding works."""
import io
import json
import struct
import sys
import tempfile
import unittest
import wave
from pathlib import Path
from unittest.mock import patch
from argparse import Namespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import ea_mt10_pcm_equivalence_v22 as tool


def write_wav(path, samples, rate=22050, channels=1):
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(channels)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(struct.pack("<" + "h" * len(samples), *samples))


class PcmEquivalenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.a = self.home / "a.wav"
        self.b = self.home / "b.wav"

    def test_same_pcm_hashes_equal(self):
        write_wav(self.a, [0, 5, -7, 30])
        write_wav(self.b, [0, 5, -7, 30])
        report = tool.compare_wavs(self.a, self.b)
        self.assertTrue(report["exact_pcm_match"])
        self.assertTrue(report["pcm_hash_matches"])
        self.assertEqual(report["original"]["pcm_frames"], 4)

    def test_one_sample_change_is_not_equal(self):
        write_wav(self.a, [0, 5, -7, 30])
        write_wav(self.b, [0, 5, -8, 30])
        report = tool.compare_wavs(self.a, self.b)
        self.assertFalse(report["exact_pcm_match"])
        self.assertTrue(report["metadata_matches"])
        self.assertFalse(report["pcm_hash_matches"])

    def test_same_pcm_wrong_sample_rate_fails(self):
        write_wav(self.a, [1, 2, 3])
        write_wav(self.b, [1, 2, 3], rate=24000)
        report = tool.compare_wavs(self.a, self.b)
        self.assertFalse(report["exact_pcm_match"])
        self.assertTrue(report["pcm_hash_matches"])
        self.assertFalse(report["metadata_matches"])

    def test_same_pcm_wrong_channel_count_fails(self):
        write_wav(self.a, [1, 2, 3, 4], channels=1)
        write_wav(self.b, [1, 2, 3, 4], channels=2)
        report = tool.compare_wavs(self.a, self.b)
        self.assertFalse(report["exact_pcm_match"])

    def test_stereo_pcm_supported(self):
        write_wav(self.a, [1, -1, 2, -2, 3, -3], channels=2)
        write_wav(self.b, [1, -1, 2, -2, 3, -3], channels=2)
        self.assertTrue(tool.compare_wavs(self.a, self.b)["exact_pcm_match"])

    def test_empty_wav_rejected(self):
        write_wav(self.a, [])
        with self.assertRaises(tool.AudioCheckError):
            tool.inspect_pcm16_wav(self.a)

    def test_missing_wav_rejected(self):
        with self.assertRaises(tool.AudioCheckError):
            tool.inspect_pcm16_wav(self.home / "missing.wav")

    def test_stream_must_start_schl(self):
        wrong = self.home / "wrong.asf"
        wrong.write_bytes(b"RIFF" + b"\0" * 32)
        with self.assertRaises(tool.AudioCheckError):
            tool.assert_schl(wrong)

    def test_stream_sha256_and_size(self):
        stream = self.home / "clip.asf"
        stream.write_bytes(b"SCHl" + b"\x01" * 4)
        result = tool.assert_schl(stream)
        self.assertEqual(result["bytes"], 8)
        self.assertEqual(len(result["sha256"]), 64)

    def test_report_refuses_overwrite(self):
        path = self.home / "report.json"
        tool.save_new_report(path, {"x": 1})
        with self.assertRaises(tool.AudioCheckError):
            tool.save_new_report(path, {"x": 2})
        self.assertEqual(json.loads(path.read_text()), {"x": 1})

    def test_wav_cli_exact_and_different_exit_codes(self):
        write_wav(self.a, [10, 11])
        write_wav(self.b, [10, 11])
        with patch("builtins.print"):
            self.assertEqual(tool.main(["compare-wavs", str(self.a), str(self.b)]), 0)
        write_wav(self.b, [10, 12])
        with patch("builtins.print"):
            self.assertEqual(tool.main(["compare-wavs", str(self.a), str(self.b)]), 1)

    def test_invalid_cli_file_returns_two(self):
        with patch("builtins.print"):
            with patch("sys.stderr", new_callable=io.StringIO):
                self.assertEqual(tool.main(["compare-wavs", str(self.a), str(self.b)]), 2)

    def test_decode_pair_with_mock_decoder(self):
        source = self.home / "original.asf"
        experiment = self.home / "pc_shape.asf"
        source.write_bytes(b"SCHl\x08\x00\x00\x00")
        experiment.write_bytes(b"SCHl\x0c\x00\x00\x00")
        out = self.home / "lab-output"
        args = Namespace(
            original=source, experimental=experiment,
            out_dir=out, decoder="fake-vgmstream", timeout=5, keep_wavs=False
        )

        def synthetic_decode(_decoder, _source, destination, _timeout):
            write_wav(destination, [100, -200, 300, -400])

        with patch.object(tool, "resolve_decoder", return_value=sys.executable):
            with patch.object(tool, "decode_one", side_effect=synthetic_decode):
                with patch("builtins.print"):
                    exit_code = tool.decode_pair_command(args)
        self.assertEqual(exit_code, 0)
        report = json.loads((out / "report.json").read_text())
        self.assertTrue(report["comparison"]["exact_pcm_match"])
        self.assertFalse((out / "original_decoded.wav").exists())
        self.assertFalse((out / "experimental_decoded.wav").exists())
        self.assertEqual(report["source_streams"]["original"]["bytes"], 8)

    def test_decode_pair_refuses_existing_directory(self):
        source = self.home / "original.asf"
        source.write_bytes(b"SCHl\x00")
        experiment = self.home / "pc_shape.asf"
        experiment.write_bytes(b"SCHl\x01")
        out = self.home / "already-here"
        out.mkdir()
        args = Namespace(
            original=source, experimental=experiment,
            out_dir=out, decoder="mock", timeout=5, keep_wavs=False
        )
        with patch.object(tool, "resolve_decoder", return_value=sys.executable):
            with self.assertRaises(tool.AudioCheckError):
                tool.decode_pair_command(args)

    def test_decode_pair_rejects_identical_sources(self):
        source = self.home / "original.asf"
        source.write_bytes(b"SCHl\x00")
        args = Namespace(
            original=source, experimental=source,
            out_dir=self.home / "newdir", decoder="mock", timeout=5,
            keep_wavs=False
        )
        with self.assertRaises(tool.AudioCheckError):
            tool.decode_pair_command(args)

    def test_missing_vgmstream_cli_is_explained(self):
        with patch.object(tool.shutil, "which", return_value=None):
            with self.assertRaises(tool.AudioCheckError):
                tool.resolve_decoder("definitely-not-a-real-decoder-123")


if __name__ == "__main__":
    unittest.main()
