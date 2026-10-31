"""V34 synthetic native IDX profile audit tests. No game archive data."""
import io
import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import experimental_native_idx_audit_v34 as v34
from ea_mt10_multiframe_scdl_v30 import make_single_block_stream
from ea_mt10_multiblock_continuity_v29 import make_ps2_stream


class NativeIDXTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.a = make_single_block_stream()
        self.b = make_ps2_stream()
        self.idx = self.home / "source.idx"
        self.big = self.home / "source.big"
        self.offsets = (32, 32 + len(self.a) + 19)
        self.big.write_bytes(b"\x00" * 32 + self.a + b"\x00" * 19 + self.b)
        self.idx.write_bytes(v34.make_synthetic_idx(
            self.big.stat().st_size, list(self.offsets)
        ))

    def test_offset_table_parses_two_records(self):
        got = v34.detect_table(self.idx.read_bytes(), self.big.stat().st_size)
        self.assertEqual(got["declared_records"], 2)
        self.assertEqual(got["endian"], "little")
        self.assertEqual([x["big_offset"] for x in got["records"]], list(self.offsets))

    def test_ids_are_opaque_not_group_claims(self):
        got = v34.audit(self.idx, self.big)
        self.assertFalse(got["raw_id_semantics_known"])
        self.assertFalse(got["group_or_police_event_identity_confirmed"])
        self.assertFalse(got["source_profile_proven_for_undercover_ps2"])
        self.assertEqual(got["records"][0]["raw_id"], 900)

    def test_idx_table_has_expected_size(self):
        self.assertEqual(self.idx.stat().st_size, 0x58 + 2 * 16)

    def test_record_spans_include_padding(self):
        got = v34.audit(self.idx, self.big)
        self.assertEqual(got["records"][0]["big_span_bytes"], len(self.a) + 19)
        self.assertEqual(got["records"][1]["big_span_bytes"], len(self.b))
        self.assertEqual(got["schl_inside_index_span"], 1)
        self.assertEqual(got["exact_schl_spans"], 1)

    def test_records_match_independently_validated_schl(self):
        got = v34.audit(self.idx, self.big)
        self.assertEqual(got["records"][0]["schl_length_bytes"], len(self.a))
        self.assertEqual(got["records"][1]["schl_length_bytes"], len(self.b))
        self.assertEqual(got["records"][0]["schl_samples"], 1296)

    def test_unsupported_other_record_marked_not_audio(self):
        first, second = self.offsets
        broken = bytearray(self.big.read_bytes())
        broken[second:second+4] = b"NOPE"
        self.big.write_bytes(broken)
        got = v34.audit(self.idx, self.big)
        self.assertEqual(got["invalid_or_other_streams"], 1)
        self.assertEqual(got["records"][1]["schl_status"],
                         "not_supported_mono_ps2_v3_mt10_schl")

    def test_single_probe_limit_preserves_unprobed(self):
        got = v34.audit(self.idx, self.big, probe_limit=1)
        self.assertEqual(got["probed_records"], 1)
        self.assertEqual(got["records"][1]["schl_status"], "not_probed")

    def test_bad_probe_limit_rejected(self):
        with self.assertRaises(v34.NativeIDXError):
            v34.audit(self.idx, self.big, probe_limit=0)

    def test_big_endian_profile_supported(self):
        self.idx.write_bytes(v34.make_synthetic_idx(
            self.big.stat().st_size, list(self.offsets), "big"
        ))
        got = v34.audit(self.idx, self.big)
        self.assertEqual(got["endian"], "big")
        self.assertEqual(got["exact_schl_spans"], 1)

    def test_wrong_explicit_endian_rejected(self):
        with self.assertRaises(v34.NativeIDXError):
            v34.detect_table(self.idx.read_bytes(), self.big.stat().st_size, "big")

    def test_truncated_idx_table_rejected(self):
        self.idx.write_bytes(self.idx.read_bytes()[:-5])
        with self.assertRaises(v34.NativeIDXError):
            v34.audit(self.idx, self.big)

    def test_impossible_count_rejected(self):
        damaged = bytearray(self.idx.read_bytes())
        struct.pack_into("<I", damaged, 0x54, 0xFFFFFFFF)
        self.idx.write_bytes(damaged)
        with self.assertRaises(v34.NativeIDXError):
            v34.audit(self.idx, self.big)

    def test_out_of_order_offsets_rejected(self):
        damaged = bytearray(self.idx.read_bytes())
        struct.pack_into("<I", damaged, 0x58 + 16 + 12, 1)
        self.idx.write_bytes(damaged)
        with self.assertRaises(v34.NativeIDXError):
            v34.audit(self.idx, self.big)

    def test_duplicate_offsets_rejected(self):
        damaged = bytearray(self.idx.read_bytes())
        struct.pack_into("<I", damaged, 0x58 + 16 + 12, self.offsets[0])
        self.idx.write_bytes(damaged)
        with self.assertRaises(v34.NativeIDXError):
            v34.audit(self.idx, self.big)

    def test_offset_beyond_big_rejected(self):
        damaged = bytearray(self.idx.read_bytes())
        struct.pack_into("<I", damaged, 0x58 + 16 + 12, 999999)
        self.idx.write_bytes(damaged)
        with self.assertRaises(v34.NativeIDXError):
            v34.audit(self.idx, self.big)

    def test_idx_trailing_bytes_are_not_silently_ignored(self):
        self.idx.write_bytes(self.idx.read_bytes() + b"\xDE\xAD")
        got = v34.audit(self.idx, self.big)
        self.assertEqual(got["trailing_idx_bytes"], 2)

    def test_no_audio_bytes_are_exported(self):
        got = v34.audit(self.idx, self.big)
        self.assertTrue(got["no_audio_bytes_exported"])
        self.assertFalse(got["real_decoder_executed"])
        self.assertFalse(got["game_runtime_tested"])

    def test_metadata_only_new_json_report(self):
        output = self.home / "audit.json"
        with patch("sys.stdout", new_callable=io.StringIO):
            code = v34.main(["audit", "--idx", str(self.idx), "--big", str(self.big),
                             "--report", str(output)])
        self.assertEqual(code, 0)
        self.assertTrue(output.exists())
        data = json.loads(output.read_text())
        self.assertEqual(data["declared_records"], 2)
        self.assertEqual(sorted(x.name for x in self.home.iterdir()),
                         ["audit.json", "source.big", "source.idx"])

    def test_refuse_overwrite_existing_report(self):
        output = self.home / "audit.json"
        output.write_text("KEEP")
        with patch("sys.stderr", new_callable=io.StringIO):
            code = v34.main(["audit", "--idx", str(self.idx), "--big", str(self.big),
                             "--report", str(output)])
        self.assertEqual(code, 2)
        self.assertEqual(output.read_text(), "KEEP")

    def test_refuse_source_path_as_report(self):
        with patch("sys.stderr", new_callable=io.StringIO):
            code = v34.main(["audit", "--idx", str(self.idx), "--big", str(self.big),
                             "--report", str(self.idx)])
        self.assertEqual(code, 2)

    def test_missing_big_rejected(self):
        with self.assertRaises(v34.NativeIDXError):
            v34.audit(self.idx, self.home / "missing.big")

    def test_cannot_assume_group_id_from_raw_id(self):
        report = v34.audit(self.idx, self.big)
        record = report["records"][0]
        self.assertIn("raw_id", record)
        self.assertNotIn("group_id", record)
        self.assertNotIn("event_id", record)

    def test_ambiguous_size_without_schl_is_not_fatal_parsing_error(self):
        big = bytearray(self.big.read_bytes())
        start = self.offsets[0]
        struct.pack_into("<I", big, start + 4, 0xFFFFFFFF)
        self.big.write_bytes(big)
        report = v34.audit(self.idx, self.big)
        self.assertEqual(report["invalid_or_other_streams"], 1)


if __name__ == "__main__":
    unittest.main()
