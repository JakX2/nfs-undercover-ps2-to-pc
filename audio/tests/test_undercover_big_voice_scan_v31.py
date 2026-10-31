"""V31 scanner tests. Inputs are generated original synthetic MT10, never game files."""
import io
import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import undercover_big_voice_scan_v31 as v31
from ea_mt10_multiframe_scdl_v30 import make_single_block_stream
from ea_mt10_multiblock_continuity_v29 import make_ps2_stream


class BigScannerV31Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        self.first = make_single_block_stream()
        self.second = make_ps2_stream()
        self.prefix = b"NOISE" * 5 + b"SCHl\xff\xff\xff\xff" + b"a" * 13
        self.offset1 = len(self.prefix)
        self.offset2 = self.offset1 + len(self.first) + 7
        self.big = self.home / "synthetic.BIG"
        self.big.write_bytes(
            self.prefix + self.first + b"b" * 7 + self.second + b"tail"
        )

    def test_scan_finds_both_audio_streams(self):
        records = v31.scan_big(self.big)
        self.assertEqual([r["offset"] for r in records],
                         [self.offset1, self.offset2])
        self.assertEqual([r["blocks"] for r in records], [1, 3])

    def test_scan_magic_at_small_chunk_boundaries(self):
        values = v31.scan_big(self.big, scan_block=7)
        self.assertEqual([x["offset"] for x in values],
                         [self.offset1, self.offset2])

    def test_scan_accepts_large_scan_block(self):
        values = v31.scan_big(self.big, scan_block=65536)
        self.assertEqual(len(values), 2)

    def test_probe_validates_rate_and_samples(self):
        with self.big.open("rb") as source:
            p = v31.probe_at(source, self.offset1, self.big.stat().st_size)
        self.assertEqual((p["rate_hz"], p["samples"], p["codec2"]),
                         (22050, 1296, 4))
        self.assertEqual(p["length"], len(self.first))

    def test_probe_skips_false_schl_header(self):
        with self.big.open("rb") as source:
            with self.assertRaises(v31.BIGProbeError):
                v31.probe_at(source, len(b"NOISE") * 5, self.big.stat().st_size)

    def test_extract_exact_original_file(self):
        data, record = v31.extract_at(self.big, self.offset2)
        self.assertEqual(data, self.second)
        self.assertEqual(record["blocks"], 3)

    def test_extract_wrong_offset_is_rejected(self):
        with self.assertRaises(v31.BIGProbeError):
            v31.extract_at(self.big, self.offset1 + 10)

    def test_scan_limit(self):
        values = v31.scan_big(self.big, max_results=1)
        self.assertEqual(len(values), 1)
        self.assertEqual(values[0]["offset"], self.offset1)

    def test_invalid_scan_limits_rejected(self):
        with self.assertRaises(v31.BIGProbeError):
            v31.scan_big(self.big, max_results=0)
        with self.assertRaises(v31.BIGProbeError):
            v31.scan_big(self.big, max_results=30000)

    def test_tiny_scan_block_rejected(self):
        with self.assertRaises(v31.BIGProbeError):
            v31.scan_big(self.big, scan_block=3)

    def test_missing_big_rejected(self):
        with self.assertRaises(v31.BIGProbeError):
            v31.scan_big(self.home / "missing.BIG")

    def test_truncated_audio_rejected(self):
        broken = self.home / "truncated.BIG"
        broken.write_bytes(self.first[:-15])
        self.assertEqual(v31.scan_big(broken), [])

    def test_changed_sccl_count_rejected(self):
        broken = bytearray(self.first)
        off = struct.unpack_from("<I", broken, 4)[0]
        struct.pack_into("<I", broken, off + 8, 7)
        path = self.home / "bad-count.BIG"
        path.write_bytes(broken)
        self.assertEqual(v31.scan_big(path), [])

    def test_changed_header_codec_rejected(self):
        broken = self.first.replace(b"\xA0\x01\x04", b"\xA0\x01\x00", 1)
        self.assertNotEqual(broken, self.first)
        path = self.home / "pcm.BIG"
        path.write_bytes(broken)
        self.assertEqual(v31.scan_big(path), [])

    def test_untrusted_magic_data_not_returned(self):
        bad = self.home / "random.BIG"
        bad.write_bytes(b"abc" + b"SCHl" + b"\xff" * 60)
        self.assertEqual(v31.scan_big(bad), [])

    def test_verify_requires_independent_decoder(self):
        with self.assertRaises(v31.BIGProbeError):
            v31.verify_at(self.big, self.offset1, "")

    def test_verify_rejects_failed_pcm_comparison(self):
        fail = {"real_decoder_executed": True, "pcm_equivalent": False}
        with patch.object(v31, "run_pair", return_value=fail):
            with self.assertRaises(v31.BIGProbeError):
                v31.verify_at(self.big, self.offset1, "fake-vgmstream")

    def test_verify_rejects_structural_only_report(self):
        fail = {"real_decoder_executed": False, "pcm_equivalent": None}
        with patch.object(v31, "run_pair", return_value=fail):
            with self.assertRaises(v31.BIGProbeError):
                v31.verify_at(self.big, self.offset1, "fake-vgmstream")

    def test_verified_report_never_claims_game_provenance(self):
        fake = {"real_decoder_executed": True, "pcm_equivalent": True}
        with patch.object(v31, "run_pair", return_value=fake):
            result = v31.verify_at(self.big, self.offset2, "fake-vgmstream")
        self.assertEqual(result["big_offset"], self.offset2)
        self.assertFalse(result["actual_undercover_provenance_confirmed"])
        self.assertFalse(result["carbon_pc_runtime_tested"])

    def test_scan_cli_outputs_no_audio(self):
        with patch("sys.stdout", new_callable=io.StringIO) as out:
            rc = v31.main(["scan", "--big", str(self.big)])
        self.assertEqual(rc, 0)
        obj = json.loads(out.getvalue())
        self.assertEqual(obj["bytes_exported"], 0)
        self.assertFalse(obj["audio_decoded"])
        self.assertEqual(obj["matching_candidates"], 2)

    def test_scan_report_not_overwritten(self):
        dest = self.home / "report.json"
        dest.write_text("original")
        with patch("sys.stderr", new_callable=io.StringIO):
            rc = v31.main(["scan", "--big", str(self.big), "--report", str(dest)])
        self.assertEqual(rc, 2)
        self.assertEqual(dest.read_text(), "original")

    def test_scan_report_created_when_new(self):
        dest = self.home / "new-report.json"
        with patch("sys.stdout", new_callable=io.StringIO):
            rc = v31.main(["scan", "--big", str(self.big), "--report", str(dest)])
        self.assertEqual(rc, 0)
        self.assertEqual(len(json.loads(dest.read_text())["candidates"]), 2)

    def test_verify_cli_refuses_existing_private_folder(self):
        dest = self.home / "existing"
        dest.mkdir()
        with patch("sys.stderr", new_callable=io.StringIO):
            rc = v31.main(["verify", "--big", str(self.big),
                           "--offset", str(self.offset1),
                           "--decoder", "fake", "--out-dir", str(dest)])
        self.assertEqual(rc, 2)

    def test_verify_cli_saves_json_without_game_media(self):
        dest = self.home / "private-result"
        with patch.object(v31, "verify_at", return_value={"pcm_equivalent": True}):
            with patch("sys.stdout", new_callable=io.StringIO):
                rc = v31.main(["verify", "--big", str(self.big),
                               "--offset", hex(self.offset1), "--decoder", "fake",
                               "--out-dir", str(dest)])
        self.assertEqual(rc, 0)
        self.assertEqual(sorted(x.name for x in dest.iterdir()), ["report.json"])

    def test_offset_argument_rejects_negative(self):
        with self.assertRaises(Exception):
            v31.int_offset("-1")

    def test_fixture_contains_two_distinct_scdl_arrangements(self):
        a, b = (v31.extract_at(self.big, x)[1] for x in (self.offset1, self.offset2))
        self.assertEqual((a["blocks"], b["blocks"]), (1, 3))
        self.assertEqual(a["samples"], b["samples"])


if __name__ == "__main__":
    unittest.main()
