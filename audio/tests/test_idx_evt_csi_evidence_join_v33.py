"""V33 original synthetic metadata graph tests. No game files or game audio."""
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import idx_evt_csi_evidence_join_v33 as v33


class EvidenceGraphTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.home = Path(self.temporary.name)
        self.scan = self.home / "scan.json"
        self.triage = self.home / "triage.json"
        self.idx = self.home / "idx.csv"
        self.evt = self.home / "evt.csv"
        self.csi = self.home / "csi.csv"
        self.scan.write_text(json.dumps({
            "format": "NFS_AUDIO_V31_BIG_SCHL_SCANNER",
            "candidates": [
                {"offset": 101, "length": 110, "samples": 432, "blocks": 1},
                {"offset": 300, "length": 150, "samples": 864, "blocks": 2},
                {"offset": 900, "length": 200, "samples": 1296, "blocks": 3},
            ]
        }))
        self.triage.write_text(json.dumps({
            "format": "NFS_AUDIO_V32_PRIVATE_BIG_DECODE_TRIAGE",
            "outcomes": [
                {"offset": 101, "source_bytes": 110,
                 "status": "independent_decoder_pcm_equal",
                 "original_pcm_sha256": "a" * 64,
                 "converted_pcm_sha256": "a" * 64},
                {"offset": 300, "source_bytes": 150,
                 "status": "decode_or_validation_failed"},
            ]
        }))
        self.idx.write_text(
            "group_id,substream,big_offset,stream_length\n"
            "42,0,101,110\n"
            "43,1,300,\n"
            "44,2,900,999\n"
        )
        self.evt.write_text(
            "event_id,group_id\n"
            "EV_POLICE_A,42\n"
            "EV_POLICE_B,42\n"
            "EV_OTHER,43\n"
            "EV_UNKNOWN,44\n"
        )
        self.csi.write_text(
            "event_id,event_name,classification\n"
            "EV_POLICE_A,Dispatch A,police\n"
            "EV_POLICE_B,Dispatch B,police\n"
            "EV_OTHER,Shop FX,other\n"
        )

    def build(self, triage=True):
        return v33.make_report(
            self.scan, self.idx, self.evt, self.csi,
            self.triage if triage else None
        )

    def test_full_chain_has_two_named_event_candidates(self):
        report = self.build()
        candidate = report["candidates"][0]
        m = candidate["index_matches"][0]
        self.assertEqual(m["idx_match"], "offset_and_length")
        self.assertEqual([x["event_id"] for x in m["event_links"]],
                         ["EV_POLICE_A", "EV_POLICE_B"])
        self.assertEqual(candidate["operator_police_labeled_event_candidates"], 2)
        self.assertEqual(report["counts"]["exact_idx_evt_csi_police_labeled"], 1)

    def test_pcm_match_requires_v32_result(self):
        result = self.build()
        self.assertEqual(result["candidates"][0]["decoder_pcm_status"],
                         "independent_decoder_pcm_equal")
        self.assertEqual(result["candidates"][1]["decoder_pcm_status"],
                         "decode_or_validation_failed")
        self.assertEqual(result["candidates"][2]["decoder_pcm_status"],
                         "not_decoder_tested")
        self.assertEqual(result["counts"]["real_decoder_pcm_equal"], 1)

    def test_offset_only_never_counts_as_exact(self):
        result = self.build()
        item = result["candidates"][1]
        self.assertEqual(item["index_matches"][0]["idx_match"], "offset_only")
        self.assertEqual(item["operator_police_labeled_event_candidates"], 0)

    def test_mismatched_length_blocks_event_link(self):
        result = self.build()
        candidate = result["candidates"][2]
        m = candidate["index_matches"][0]
        self.assertEqual(m["idx_match"], "offset_but_length_mismatch")
        self.assertEqual(m["event_links"], [])
        self.assertEqual(result["counts"]["idx_length_mismatch"], 1)

    def test_never_claims_actual_original_police_voices(self):
        result = self.build()
        self.assertFalse(result["actual_police_voice_heard_or_confirmed"])
        self.assertFalse(result["original_game_provenance_independently_verified"])
        self.assertFalse(result["carbon_pc_runtime_verified"])
        for item in result["candidates"]:
            self.assertFalse(item["actual_police_voice_heard_or_confirmed"])

    def test_incomplete_csi_only_has_unnamed_event(self):
        self.idx.write_text("group_id,substream,big_offset,stream_length\n44,2,900,200\n")
        result = self.build(triage=False)
        link = result["candidates"][2]["index_matches"][0]["event_links"][0]
        self.assertFalse(link["csi_name_present"])
        self.assertIsNone(link["event_name"])
        self.assertIsNone(link["classification_supplied"])

    def test_multi_idx_entries_at_same_offset_preserved(self):
        with self.idx.open("a") as f:
            f.write("45,7,101,110\n")
        with self.evt.open("a") as f:
            f.write("EV_EXTRA,45\n")
        result = self.build()
        self.assertEqual(len(result["candidates"][0]["index_matches"]), 2)
        self.assertEqual(result["counts"]["multiple_idx_entries_at_same_offset"], 1)

    def test_mismatched_v32_size_rejected(self):
        report = json.loads(self.triage.read_text())
        report["outcomes"][0]["source_bytes"] = 111
        self.triage.write_text(json.dumps(report))
        with self.assertRaises(v33.AttributionError):
            self.build()

    def test_unscanned_triage_offset_rejected(self):
        report = json.loads(self.triage.read_text())
        report["outcomes"][0]["offset"] = 222
        self.triage.write_text(json.dumps(report))
        with self.assertRaises(v33.AttributionError):
            self.build()

    def test_unmatched_idx_remains_unmatched(self):
        self.idx.write_text("group_id,substream,big_offset,stream_length\n43,0,9999,100\n")
        result = self.build()
        self.assertTrue(all(not c["index_matches"] for c in result["candidates"]))

    def test_input_sha256_values_are_recorded(self):
        report = self.build()
        self.assertEqual(len(report["input_sha256"]["idx_export_csv"]), 64)
        self.assertEqual(len(report["input_sha256"]["v32_triage_json"]), 64)

    def test_no_triage_option(self):
        report = self.build(triage=False)
        self.assertEqual(report["candidates"][0]["decoder_pcm_status"], "not_decoder_tested")
        self.assertIsNone(report["input_sha256"]["v32_triage_json"])

    def test_duplicate_idx_key_rejected(self):
        with self.idx.open("a") as f:
            f.write("42,0,999,444\n")
        with self.assertRaises(v33.AttributionError):
            v33.load_idx(self.idx)

    def test_duplicate_evt_edge_rejected(self):
        with self.evt.open("a") as f:
            f.write("EV_POLICE_A,42\n")
        with self.assertRaises(v33.AttributionError):
            v33.load_evt(self.evt)

    def test_duplicate_csi_id_rejected(self):
        with self.csi.open("a") as f:
            f.write("EV_POLICE_A,Forged duplicate,other\n")
        with self.assertRaises(v33.AttributionError):
            v33.load_csi(self.csi)

    def test_reject_missing_columns(self):
        self.idx.write_text("group_id,big_offset\n42,101\n")
        with self.assertRaises(v33.AttributionError):
            v33.load_idx(self.idx)

    def test_reject_extra_or_malformed_csv_values(self):
        self.csi.write_text(
            "event_id,event_name,classification\nEV_A,Test,police,extra\n"
        )
        with self.assertRaises(v33.AttributionError):
            v33.load_csi(self.csi)

    def test_reject_forged_status_with_conflicting_hashes(self):
        data = json.loads(self.triage.read_text())
        data["outcomes"][0]["converted_pcm_sha256"] = "b" * 64
        self.triage.write_text(json.dumps(data))
        with self.assertRaises(v33.AttributionError):
            self.build()

    def test_reject_v32_duplicate_offset(self):
        data = json.loads(self.triage.read_text())
        data["outcomes"].append(data["outcomes"][0])
        self.triage.write_text(json.dumps(data))
        with self.assertRaises(v33.AttributionError):
            self.build()

    def test_reject_v31_duplicate_offset(self):
        data = json.loads(self.scan.read_text())
        data["candidates"].append(data["candidates"][0])
        self.scan.write_text(json.dumps(data))
        with self.assertRaises(v33.AttributionError):
            self.build()

    def test_accept_decimal_numbers_with_leading_zeros(self):
        self.idx.write_text("group_id,substream,big_offset,stream_length\n042,00,00101,00110\n")
        result = self.build(triage=False)
        self.assertEqual(result["candidates"][0]["index_matches"][0]["group_id"], 42)

    def test_hex_group_and_offset_supported(self):
        self.idx.write_text("group_id,substream,big_offset,stream_length\n0x2a,0,0x65,0x6e\n")
        result = self.build(triage=False)
        self.assertEqual(result["candidates"][0]["index_matches"][0]["idx_match"],
                         "offset_and_length")

    def test_unknown_csi_classification_rejected(self):
        self.csi.write_text(
            "event_id,event_name,classification\nEV_A,Test,guessed_police\n"
        )
        with self.assertRaises(v33.AttributionError):
            v33.load_csi(self.csi)

    def test_cli_refuses_existing_json(self):
        outfile = self.home / "report.json"
        outfile.write_text("keep")
        with patch("sys.stderr", new_callable=io.StringIO):
            status = v33.main([
                "join", "--scan", str(self.scan), "--idx", str(self.idx),
                "--evt", str(self.evt), "--csi", str(self.csi),
                "--report", str(outfile),
            ])
        self.assertEqual(status, 2)
        self.assertEqual(outfile.read_text(), "keep")

    def test_cli_generates_new_json_without_game_data(self):
        outfile = self.home / "joined.json"
        with patch("sys.stdout", new_callable=io.StringIO):
            code = v33.main([
                "join", "--scan", str(self.scan), "--idx", str(self.idx),
                "--evt", str(self.evt), "--csi", str(self.csi),
                "--triage", str(self.triage), "--report", str(outfile),
            ])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(outfile.read_text())["joined_candidates"], 3)
        self.assertEqual(len(list(self.home.glob("*.asf"))), 0)

    def test_self_test_never_confirmed_game_audio(self):
        result = v33.self_test()
        self.assertTrue(result["exact_candidate_with_decoded_pcm"])
        self.assertFalse(result["actual_police_voice_confirmed"])

    def test_out_of_range_uint32_idx_rejected(self):
        self.idx.write_text(
            "group_id,substream,big_offset,stream_length\n4294967296,0,101,110\n"
        )
        with self.assertRaises(v33.AttributionError):
            v33.load_idx(self.idx)


if __name__ == "__main__":
    unittest.main()
