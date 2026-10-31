"""V23 synthetic tests: no copyrighted or actual EA-MT10 audio."""
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import vgmstream_metadata_preflight_v23 as v23


SAMPLE = """metadata for test.asf
sample rate: 22050 Hz
channels: 1
stream total samples: 34567 (0:01.568 seconds)
encoding: EA MicroTalk
layout: blocked
metadata from: Electronic Arts SCHl
bitrate: 42 kbps
"""


class MetadataTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        self.a = self.home / "undercover.asf"
        self.b = self.home / "pcshape.asf"
        self.a.write_bytes(b"SCHl\x0c\x00\x00\x00" + b"A" * 20)
        self.b.write_bytes(b"SCHl\x10\x00\x00\x00" + b"B" * 20)
        self.decoder = self.home / "vgmstream-cli"
        self.decoder.write_bytes(b"fake executable for synthetic tests")

    def test_parses_sample_rate_channels_samples_encoding(self):
        data = v23.parse_metadata(SAMPLE)
        self.assertEqual(data["sample_rate_hz"], 22050)
        self.assertEqual(data["channels"], 1)
        self.assertEqual(data["total_samples"], 34567)
        self.assertEqual(data["encoding"], "EA MicroTalk")

    def test_ignores_unknown_metadata_fields(self):
        self.assertNotIn("bitrate", v23.parse_metadata(SAMPLE))

    def test_missing_required_fields_rejected(self):
        with self.assertRaises(v23.ProbeError):
            v23.parse_metadata("sample rate: 22050 Hz\nchannels: 2\n")

    def test_nonnumeric_sample_rate_rejected(self):
        with self.assertRaises(v23.ProbeError):
            v23.parse_metadata(SAMPLE.replace("22050", "foo"))

    def test_unreasonably_large_channels_rejected(self):
        with self.assertRaises(v23.ProbeError):
            v23.parse_metadata(SAMPLE.replace("channels: 1", "channels: 99"))

    def test_bad_schl_rejected(self):
        self.a.write_bytes(b"RIFF\x10\x00\x00\x00")
        with self.assertRaises(v23.ProbeError):
            v23.check_schl(self.a)

    def test_short_schl_rejected(self):
        self.a.write_bytes(b"SCHl")
        with self.assertRaises(v23.ProbeError):
            v23.check_schl(self.a)

    def test_valid_schl_hash(self):
        info = v23.check_schl(self.a)
        self.assertEqual(info["bytes"], 28)
        self.assertEqual(len(info["sha256"]), 64)

    def test_decoder_run_metadata_only(self):
        result = SimpleNamespace(stdout=SAMPLE.encode(), stderr=b"", returncode=0)
        with patch.object(v23.subprocess, "run", return_value=result) as proc:
            parsed = v23.get_metadata(self.decoder, self.a, 10)
        args = proc.call_args.args[0]
        self.assertEqual(args[1], "-m")
        self.assertEqual(parsed["channels"], 1)

    def test_decoder_failure_is_not_success(self):
        result = SimpleNamespace(stdout=b"", stderr=b"broken", returncode=1)
        with patch.object(v23.subprocess, "run", return_value=result):
            with self.assertRaises(v23.ProbeError):
                v23.get_metadata(self.decoder, self.a, 10)

    def test_identical_paths_rejected(self):
        with self.assertRaises(v23.ProbeError):
            v23.probe_pair(self.a, self.a, self.decoder, 10)

    def test_equal_metadata_does_not_claim_pcm(self):
        with patch.object(v23, "get_metadata", return_value=v23.parse_metadata(SAMPLE)):
            result = v23.probe_pair(self.a, self.b, self.decoder, 10)
        self.assertTrue(result["metadata_match"])
        self.assertFalse(result["pcm_checked"])
        self.assertFalse(result["game_playback_checked"])

    def test_different_metadata_returns_mismatch(self):
        alternate = v23.parse_metadata(SAMPLE.replace("22050", "24000"))
        with patch.object(v23, "get_metadata", side_effect=[v23.parse_metadata(SAMPLE), alternate]):
            result = v23.probe_pair(self.a, self.b, self.decoder, 10)
        self.assertFalse(result["metadata_match"])
        self.assertFalse(result["field_matches"]["sample_rate_hz"])

    def test_existing_report_not_overwritten(self):
        out = self.home / "report.json"
        out.write_text("original")
        args = ["--original", str(self.a), "--experimental", str(self.b),
                "--decoder", str(self.decoder), "--report", str(out)]
        with patch.object(v23, "resolve_decoder", return_value=self.decoder):
            with patch("sys.stderr", new_callable=io.StringIO):
                self.assertEqual(v23.main(args), 2)
        self.assertEqual(out.read_text(), "original")

    def test_cli_writes_report_on_match(self):
        out = self.home / "output.json"
        args = ["--original", str(self.a), "--experimental", str(self.b),
                "--decoder", str(self.decoder), "--report", str(out)]
        with patch.object(v23, "resolve_decoder", return_value=self.decoder):
            with patch.object(v23, "get_metadata", return_value=v23.parse_metadata(SAMPLE)):
                with patch("sys.stdout", new_callable=io.StringIO):
                    self.assertEqual(v23.main(args), 0)
        self.assertFalse(json.loads(out.read_text())["pcm_checked"])

    def test_timeout_zero_rejected(self):
        with self.assertRaises(v23.ProbeError):
            v23.get_metadata(self.decoder, self.a, 0)


if __name__ == "__main__":
    unittest.main()
