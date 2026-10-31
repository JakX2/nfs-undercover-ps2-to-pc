"""V32 batch triage: source-only regression tests, never commercial game audio."""
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import big_mt10_batch_triage_v32 as tool
from ea_mt10_multiframe_scdl_v30 import make_single_block_stream
from ea_mt10_multiblock_continuity_v29 import make_ps2_stream
from ea_mt10_pcm_equivalence_v22 import AudioCheckError


def item(offset, samples=1296):
    return {"offset": offset, "length": 160, "samples": samples, "blocks": 1}


def successful_verification(offset):
    sha = f"{offset:064x}"
    return {
        "real_decoder_executed": True,
        "pcm_equivalent": True,
        "decoded_pcm": {
            "original": {"pcm_sha256": sha},
            "experimental": {"pcm_sha256": sha},
        },
    }


class V32BatchTriageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        self.big = self.home / "generated.BIG"
        a = make_single_block_stream()
        b = make_ps2_stream()
        self.big.write_bytes(b"JUNK" + a + b"\x00" * 17 + b)

    def test_longest_candidate_first(self):
        found = [item(10, 600), item(20, 1200), item(30, 700)]
        self.assertEqual([x["offset"] for x in tool.choose_candidates(
            found, limit=3, minimum_samples=1)], [20, 30, 10])

    def test_ties_sort_by_offset(self):
        found = [item(300), item(40), item(10)]
        selected = tool.choose_candidates(found, limit=3, minimum_samples=1)
        self.assertEqual([r["offset"] for r in selected], [10, 40, 300])

    def test_rejects_invalid_limits(self):
        with self.assertRaises(tool.TriageError):
            tool.choose_candidates([item(0)], limit=0, minimum_samples=1)
        with self.assertRaises(tool.TriageError):
            tool.choose_candidates([item(0)], limit=33, minimum_samples=1)

    def test_rejects_invalid_sample_threshold(self):
        with self.assertRaises(tool.TriageError):
            tool.choose_candidates([item(0)], limit=1, minimum_samples=0)

    def test_rejects_negative_start(self):
        with self.assertRaises(tool.TriageError):
            tool.choose_candidates([item(0)], limit=1, minimum_samples=1, start=-1)

    def test_pagination(self):
        found = [item(10, 600), item(20, 500), item(30, 400)]
        selected = tool.choose_candidates(found, limit=1, minimum_samples=1, start=1)
        self.assertEqual([r["offset"] for r in selected], [20])

    def test_minimum_sample_filter(self):
        selected = tool.choose_candidates([item(10, 400), item(20, 900)],
                                         limit=2, minimum_samples=500)
        self.assertEqual([x["offset"] for x in selected], [20])

    def test_scanner_uses_actual_synthetic_big(self):
        from undercover_big_voice_scan_v31 import scan_big
        candidates = scan_big(self.big)
        self.assertEqual(len(candidates), 2)

    def test_requires_real_decoder(self):
        with self.assertRaises(tool.TriageError):
            tool.triage(self.big, "", limit=2)

    def test_rejects_invalid_max_results(self):
        with self.assertRaises(tool.TriageError):
            tool.triage(self.big, "fake", max_results=0)

    def test_successful_batch_results_metadata_only(self):
        with patch.object(tool, "resolve_decoder", return_value="/synthetic/cli"):
            with patch.object(tool, "verify_at",
                              side_effect=lambda _b, offset, _d: successful_verification(offset)):
                result = tool.triage(self.big, "fake", limit=2)
        self.assertEqual(result["selected_count"], 2)
        self.assertEqual(result["successful_pcm_pairs"], 2)
        self.assertEqual(result["failed_pcm_pairs"], 0)
        self.assertTrue(all(x["status"] == "independent_decoder_pcm_equal"
                            for x in result["outcomes"]))
        self.assertFalse(result["extracted_audio_files_retained"])
        self.assertEqual(result["identified_police_events"], 0)
        self.assertFalse(result["carbon_pc_runtime_tested"])

    def test_failure_does_not_count_as_pcm_success(self):
        with patch.object(tool, "resolve_decoder", return_value="/synthetic/cli"):
            with patch.object(tool, "verify_at",
                              side_effect=AudioCheckError("decoder failed at private path")):
                result = tool.triage(self.big, "fake", limit=2)
        self.assertEqual(result["successful_pcm_pairs"], 0)
        self.assertEqual(result["failed_pcm_pairs"], 2)
        self.assertNotIn("private path", json.dumps(result))
        self.assertEqual(result["outcomes"][0]["error_type"], "AudioCheckError")

    def test_one_success_one_failure(self):
        count = [0]
        def fake_verify(_big, offset, _decoder):
            count[0] += 1
            if count[0] == 2:
                raise AudioCheckError("fail")
            return successful_verification(offset)
        with patch.object(tool, "resolve_decoder", return_value="/synthetic/cli"):
            with patch.object(tool, "verify_at", side_effect=fake_verify):
                result = tool.triage(self.big, "fake", limit=2)
        self.assertEqual((result["successful_pcm_pairs"], result["failed_pcm_pairs"]), (1, 1))

    def test_scan_limit_truncation_is_reported(self):
        with patch.object(tool, "resolve_decoder", return_value="/synthetic/cli"):
            with patch.object(tool, "verify_at",
                              side_effect=lambda _b, offset, _d: successful_verification(offset)):
                result = tool.triage(self.big, "fake", max_results=1, limit=2)
        self.assertEqual(result["selected_count"], 1)
        self.assertTrue(result["scan_may_be_truncated"])

    def test_empty_filter_is_not_a_success(self):
        with patch.object(tool, "resolve_decoder", return_value="/synthetic/cli"):
            result = tool.triage(self.big, "fake", minimum_samples=100000)
        self.assertEqual(result["selected_count"], 0)
        self.assertEqual(result["successful_pcm_pairs"], 0)

    def test_cli_refuses_existing_output(self):
        path = self.home / "existing"
        path.mkdir()
        with patch("sys.stderr", new_callable=io.StringIO):
            result = tool.main([
                "triage", "--big", str(self.big), "--decoder", "fake",
                "--out-dir", str(path)
            ])
        self.assertEqual(result, 2)

    def test_cli_zero_candidates_returns_three(self):
        out = self.home / "no_candidates"
        with patch.object(tool, "resolve_decoder", return_value="/synthetic/cli"):
            with patch("sys.stdout", new_callable=io.StringIO):
                result = tool.main([
                    "triage", "--big", str(self.big), "--decoder", "fake",
                    "--minimum-samples", "1000000", "--out-dir", str(out)
                ])
        self.assertEqual(result, 3)
        self.assertEqual(len(json.loads((out / "report.json").read_text())["outcomes"]), 0)

    def test_cli_writes_one_json_only(self):
        out = self.home / "results"
        with patch.object(tool, "resolve_decoder", return_value="/synthetic/cli"):
            with patch.object(tool, "verify_at",
                              side_effect=lambda _b, offset, _d: successful_verification(offset)):
                with patch("sys.stdout", new_callable=io.StringIO):
                    result = tool.main([
                        "triage", "--big", str(self.big), "--decoder", "fake",
                        "--limit", "2", "--out-dir", str(out)
                    ])
        self.assertEqual(result, 0)
        self.assertEqual([x.name for x in out.iterdir()], ["report.json"])

    def test_cli_error_returns_two(self):
        with patch("sys.stderr", new_callable=io.StringIO):
            result = tool.main([
                "triage", "--big", str(self.big), "--decoder", "/missing/decoder",
                "--out-dir", str(self.home / "new")
            ])
        self.assertEqual(result, 2)

    def test_no_police_identity_is_inferred(self):
        with patch.object(tool, "resolve_decoder", return_value="/synthetic/cli"):
            with patch.object(tool, "verify_at",
                              side_effect=lambda _b, offset, _d: successful_verification(offset)):
                report = tool.triage(self.big, "fake", limit=2)
        self.assertTrue(all(not x["police_event_identity_verified"]
                            for x in report["outcomes"]))


if __name__ == "__main__":
    unittest.main()
