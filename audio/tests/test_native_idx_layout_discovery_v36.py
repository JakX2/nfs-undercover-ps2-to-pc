"""V36 synthetic tests for IDX layout discovery from validated SCHl offsets."""
import io
import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import native_idx_layout_discovery_v36 as v36
from ea_mt10_multiframe_scdl_v30 import make_single_block_stream
from undercover_big_voice_scan_v31 import scan_big


class LayoutDiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.starts = (64, 176, 320, 456, 712)
        self.idx = self.home / "test.IDX"
        self.scan = self.home / "scan.json"
        self.idx.write_bytes(v36.fake_idx(
            list(self.starts), 0x54, 4, 16, 12, "little"
        ))
        self.scan.write_text(json.dumps({
            "format": "NFS_AUDIO_V31_BIG_SCHL_SCANNER",
            "candidates": [
                {"offset": i, "length": 100, "samples": 432, "blocks": 1}
                for i in self.starts
            ],
        }))

    def find(self, result, count_pos=0x54, gap=4, stride=16, field=12, endian="little"):
        return [
            x for x in result["displayed_layouts"]
            if (x["count_field_position"], x["record_table_start"],
                x["record_stride"], x["offset_field_position_in_record"],
                x["endian"]) == (count_pos, count_pos + gap, stride, field, endian)
        ]

    def test_recovers_original_xbox_style_hypothesis(self):
        report = v36.investigate(self.idx, self.scan)
        self.assertEqual(len(self.find(report)), 1)
        self.assertEqual(self.find(report)[0]["matching_sampled_rows"], 5)

    def test_discovers_independent_big_endian_alternative(self):
        self.idx.write_bytes(v36.fake_idx(
            list(self.starts), 0x10, 8, 12, 4, "big"
        ))
        result = v36.investigate(self.idx, self.scan)
        self.assertEqual(len(self.find(result, 0x10, 8, 12, 4, "big")), 1)

    def test_different_row_width(self):
        self.idx.write_bytes(v36.fake_idx(
            list(self.starts), 0x30, 16, 24, 8, "little"
        ))
        result = v36.investigate(self.idx, self.scan)
        self.assertEqual(len(self.find(result, 0x30, 16, 24, 8)), 1)

    def test_detects_opaque_nonmonotonic_offsets(self):
        reordered = [self.starts[2], self.starts[0], self.starts[3],
                     self.starts[1], self.starts[4]]
        self.idx.write_bytes(v36.fake_idx(reordered, 0x54, 4, 16, 12, "little"))
        result = v36.investigate(self.idx, self.scan)
        found = self.find(result)
        self.assertEqual(len(found), 1)
        self.assertFalse(found[0]["sampled_offsets_strictly_increasing"])

    def test_no_false_native_certification(self):
        report = v36.investigate(self.idx, self.scan)
        self.assertTrue(report["layout_is_not_proof_of_native_undercover_format"])
        self.assertTrue(report["unknown_idx_words_not_mapped_to_group_or_event"])
        self.assertFalse(report["real_game_audio_decoded"])
        self.assertFalse(report["carbon_runtime_tested"])
        self.assertFalse(report["displayed_layouts"][0]["undercover_ps2_format_confirmed"])

    def test_no_matches_yields_zero_candidate_layouts(self):
        self.scan.write_text(json.dumps({
            "format": "NFS_AUDIO_V31_BIG_SCHL_SCANNER",
            "candidates": [
                {"offset": i + 5000, "length": 100, "samples": 432, "blocks": 1}
                for i in self.starts
            ]
        }))
        result = v36.investigate(self.idx, self.scan)
        self.assertEqual(result["displayed_layouts"], [])
        self.assertEqual(result["qualifying_layouts_total"], 0)

    def test_rejects_empty_v31_scan(self):
        self.scan.write_text(json.dumps({
            "format": "NFS_AUDIO_V31_BIG_SCHL_SCANNER", "candidates": []
        }))
        with self.assertRaises(v36.LayoutError):
            v36.investigate(self.idx, self.scan)

    def test_malformed_scan_format_rejected(self):
        self.scan.write_text(json.dumps({"format": "WRONG", "candidates": []}))
        from idx_evt_csi_evidence_join_v33 import AttributionError
        with self.assertRaises(AttributionError):
            v36.investigate(self.idx, self.scan)

    def test_rejects_empty_idx(self):
        self.idx.write_bytes(b"")
        with self.assertRaises(v36.LayoutError):
            v36.investigate(self.idx, self.scan)

    def test_rejects_oversized_idx(self):
        with patch.object(v36, "MAX_IDX_BYTES", 100):
            with self.assertRaises(v36.LayoutError):
                v36.investigate(self.idx, self.scan)

    def test_sparse_candidate_not_falsely_promoted(self):
        # Only two hits in a five-record table cannot qualify.
        self.idx.write_bytes(v36.fake_idx(
            [self.starts[0], self.starts[1], 999, 1000, 1001],
            0x54, 4, 16, 12, "little"
        ))
        result = v36.investigate(self.idx, self.scan)
        self.assertEqual(self.find(result), [])

    def test_one_validated_offset_repeated_is_not_sufficient(self):
        self.idx.write_bytes(v36.fake_idx(
            [self.starts[0]] * 5, 0x54, 4, 16, 12, "little"
        ))
        self.assertEqual(self.find(v36.investigate(self.idx, self.scan)), [])

    def test_truncated_table_not_promoted(self):
        self.idx.write_bytes(self.idx.read_bytes()[:-5])
        self.assertEqual(self.find(v36.investigate(self.idx, self.scan)), [])

    def test_invalid_top_limits(self):
        with self.assertRaises(v36.LayoutError):
            v36.discover(self.idx.read_bytes(), set(self.starts), top=0)
        with self.assertRaises(v36.LayoutError):
            v36.discover(self.idx.read_bytes(), set(self.starts), top=21)

    def test_invalid_maximum_count(self):
        with self.assertRaises(v36.LayoutError):
            v36.discover(self.idx.read_bytes(), set(self.starts), maximum_count=2)

    def test_sampled_rows_are_balanced(self):
        indexes = v36.sampled_indices(1000)
        self.assertGreaterEqual(len(indexes), 95)
        self.assertLessEqual(len(indexes), 96)
        self.assertEqual((indexes[0], indexes[-1]), (0, 999))

    def test_small_table_all_rows_sampled(self):
        self.assertEqual(v36.sampled_indices(5), (0, 1, 2, 3, 4))

    def test_record_column_outside_record_rejected(self):
        got = v36.score_profile(
            self.idx.read_bytes(), set(self.starts), endian="little",
            count_pos=0x54, table_start=0x58, stride=16, offset_in_row=16
        )
        self.assertIsNone(got)

    def test_invalid_endian_rejected_without_crash(self):
        got = v36.score_profile(
            self.idx.read_bytes(), set(self.starts), endian="native",
            count_pos=0x54, table_start=0x58, stride=16, offset_in_row=12
        )
        self.assertIsNone(got)

    def test_candidate_count_matches_declared_count(self):
        report = v36.investigate(self.idx, self.scan)
        self.assertEqual(self.find(report)[0]["record_count"], 5)

    def test_source_hashes_are_provided(self):
        report = v36.investigate(self.idx, self.scan)
        self.assertEqual(len(report["idx_sha256"]), 64)
        self.assertEqual(len(report["v31_scan_json_sha256"]), 64)

    def test_cli_report_new_and_metadata_only(self):
        target = self.home / "report.json"
        with patch("sys.stdout", new_callable=io.StringIO):
            code = v36.main([
                "discover", "--idx", str(self.idx), "--scan", str(self.scan),
                "--report", str(target)
            ])
        self.assertEqual(code, 0)
        self.assertTrue(target.is_file())
        report = json.loads(target.read_text())
        self.assertTrue(report["read_only"])
        self.assertEqual(len(list(self.home.glob("*.asf"))), 0)

    def test_cli_never_overwrites_report(self):
        target = self.home / "report.json"
        target.write_text("KEEP")
        with patch("sys.stderr", new_callable=io.StringIO):
            code = v36.main([
                "discover", "--idx", str(self.idx), "--scan", str(self.scan),
                "--report", str(target)
            ])
        self.assertEqual(code, 2)
        self.assertEqual(target.read_text(), "KEEP")

    def test_cli_refuses_input_as_output(self):
        with patch("sys.stderr", new_callable=io.StringIO):
            code = v36.main([
                "discover", "--idx", str(self.idx), "--scan", str(self.scan),
                "--report", str(self.idx)
            ])
        self.assertEqual(code, 2)

    def test_self_test_runs_real_schl_scanner(self):
        output = v36.self_test()
        self.assertEqual(output["distinct_synthetic_layouts_found"], 2)
        self.assertTrue(output["real_schl_scanner_integrated"])
        self.assertFalse(output["game_data_used"])

    def test_three_entry_minimum(self):
        starts = {100, 200, 300}
        data = v36.fake_idx([100, 200, 300], 0x54, 4, 16, 12, "little")
        report = v36.discover(data, starts)
        self.assertEqual(len(self.find(report)), 1)

    def test_audit_file_not_mutated(self):
        before = self.idx.read_bytes()
        v36.investigate(self.idx, self.scan)
        self.assertEqual(self.idx.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
