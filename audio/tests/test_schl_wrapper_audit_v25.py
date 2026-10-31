"""V25 unit tests. Generated SCHl structures only; no actual EA-MT10 game data."""
import io
import json
import struct
import sys
import tempfile
import unittest
import wave
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import schl_wrapper_audit_v25 as tool


def chunk(tag: bytes, payload: bytes = b"") -> bytes:
    return tag + struct.pack("<I", 8 + len(payload)) + payload


def fake_schl(header=b"\x01" * 20, samples=(4, 5), alteration=b"", pad=0):
    count = chunk(b"SCCl", struct.pack("<I", len(samples)))
    blocks = b"".join(
        chunk(b"SCDl", struct.pack("<I", n) +
              b"\x00\x00\x00\x00\x01" + bytes([i]) + alteration)
        for i, n in enumerate(samples)
    )
    return chunk(b"SCHl", header) + count + blocks + chunk(b"SCEl") + b"\x00" * pad


def write_pcm_wav(path: Path, frames=(2, 1, 0, -2)):
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(22050)
        wav.writeframes(struct.pack("<" + "h" * len(frames), *frames))


class StreamStructureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.a = self.home / "original.asf"
        self.b = self.home / "pc_shape.asf"
        self.a.write_bytes(fake_schl(header=b"A" * 20))
        self.b.write_bytes(fake_schl(header=b"B" * 24))

    def test_preserves_all_chunks_after_different_headers(self):
        result = tool.compare(self.a, self.b)
        self.assertTrue(result["structurally_lossless_wrapper"])
        self.assertEqual(result["original"]["header_size"], 28)
        self.assertEqual(result["experimental"]["header_size"], 32)
        self.assertEqual(result["original"]["audio_block_count"], 2)
        self.assertEqual(result["original"]["total_scdl_samples"], 9)
        self.assertFalse(result["decoder_executed"])

    def test_sample_accounting_and_hashes(self):
        result = tool.parse_stream(fake_schl(samples=(11, 18, 23)))
        self.assertEqual(result["declared_block_count"], 3)
        self.assertEqual(result["total_scdl_samples"], 52)
        self.assertEqual(len(result["scdl_chunk_sha256"]), 3)
        self.assertEqual(result["chunk_tags"],
                         ["SCHl", "SCCl", "SCDl", "SCDl", "SCDl", "SCEl"])

    def test_changed_block_payload_is_detected(self):
        self.b.write_bytes(fake_schl(header=b"B" * 24, alteration=b"\x99"))
        result = tool.compare(self.a, self.b)
        self.assertFalse(result["structurally_lossless_wrapper"])
        self.assertFalse(result["checks"]["identical_audio_blocks"])

    def test_changed_block_sample_count_detected(self):
        self.b.write_bytes(fake_schl(header=b"B" * 24, samples=(4, 6)))
        result = tool.compare(self.a, self.b)
        self.assertFalse(result["checks"]["unchanged_block_sample_counts"])

    def test_padding_is_not_part_of_audio(self):
        self.b.write_bytes(fake_schl(header=b"B" * 24, pad=7))
        self.assertTrue(tool.compare(self.a, self.b)["structurally_lossless_wrapper"])

    def test_extra_nonzero_trailing_bytes_rejected(self):
        with self.assertRaises(tool.SCHlAuditError):
            tool.parse_stream(fake_schl() + b"\x01")

    def test_padding_over_255_rejected(self):
        with self.assertRaises(tool.SCHlAuditError):
            tool.parse_stream(fake_schl(pad=256))

    def test_missing_sccl_rejected(self):
        data = chunk(b"SCHl", b"A" * 20) + chunk(
            b"SCDl", struct.pack("<I", 4) + b"\x00" * 8
        ) + chunk(b"SCEl")
        with self.assertRaises(tool.SCHlAuditError):
            tool.parse_stream(data)

    def test_count_mismatch_rejected(self):
        data = bytearray(fake_schl())
        offset = 8 + 20 + 8
        struct.pack_into("<I", data, offset, 999)
        with self.assertRaises(tool.SCHlAuditError):
            tool.parse_stream(data)

    def test_truncated_chunk_header_rejected(self):
        with self.assertRaises(tool.SCHlAuditError):
            tool.parse_stream(fake_schl()[:-5])

    def test_oversized_chunk_rejected(self):
        data = bytearray(fake_schl())
        struct.pack_into("<I", data, 4, 0xFFFFFF)
        with self.assertRaises(tool.SCHlAuditError):
            tool.parse_stream(data)

    def test_unknown_tag_rejected(self):
        data = bytearray(fake_schl())
        data[0:4] = b"RIFF"
        with self.assertRaises(tool.SCHlAuditError):
            tool.parse_stream(data)

    def test_missing_scel_rejected(self):
        with self.assertRaises(tool.SCHlAuditError):
            tool.parse_stream(fake_schl()[:-8])

    def test_refuse_same_input_file(self):
        with self.assertRaises(tool.SCHlAuditError):
            tool.compare(self.a, self.a)

    def test_refuse_overwrite_report(self):
        report = self.home / "report.json"
        report.write_text("keep")
        with patch("sys.stderr", new_callable=io.StringIO):
            self.assertEqual(tool.main([
                "--original", str(self.a), "--experimental", str(self.b),
                "--report", str(report),
            ]), 2)
        self.assertEqual(report.read_text(), "keep")

    def test_structural_cli_report(self):
        report = self.home / "report.json"
        with patch("sys.stdout", new_callable=io.StringIO):
            code = tool.main([
                "--original", str(self.a), "--experimental", str(self.b),
                "--report", str(report),
            ])
        self.assertEqual(code, 0)
        data = json.loads(report.read_text())
        self.assertTrue(data["passed"])
        self.assertFalse(data["decoder_executed"])

    def test_optional_decoder_compares_real_pcm_structures(self):
        def synthetic_decode(_decoder, _source, target, _timeout):
            write_pcm_wav(target)
        with patch.object(tool, "resolve_decoder", return_value=sys.executable):
            with patch.object(tool, "decode_one", side_effect=synthetic_decode):
                with patch("sys.stdout", new_callable=io.StringIO):
                    report = self.home / "decoded.json"
                    code = tool.main([
                        "--original", str(self.a), "--experimental", str(self.b),
                        "--decoder", "mock", "--report", str(report),
                    ])
        self.assertEqual(code, 0)
        data = json.loads(report.read_text())
        self.assertTrue(data["decoder_executed"])
        self.assertTrue(data["real_decoder"]["decoded_pcm_comparison"]["exact_pcm_match"])

    def test_decode_mismatch_fails_even_with_matching_blocks(self):
        def synth_decode(_decoder, source, target, _timeout):
            write_pcm_wav(target, frames=(1, 2) if source == self.a else (1, 3))
        with patch.object(tool, "resolve_decoder", return_value=sys.executable):
            with patch.object(tool, "decode_one", side_effect=synth_decode):
                with patch("sys.stdout", new_callable=io.StringIO):
                    report = self.home / "mismatch.json"
                    code = tool.main([
                        "--original", str(self.a), "--experimental", str(self.b),
                        "--decoder", "mock", "--report", str(report),
                    ])
        self.assertEqual(code, 1)
        data = json.loads(report.read_text())
        self.assertTrue(data["structurally_lossless_wrapper"])
        self.assertFalse(data["passed"])

    def test_missing_recording_returns_error(self):
        with patch("sys.stderr", new_callable=io.StringIO):
            self.assertEqual(tool.main([
                "--original", str(self.home / "missing"),
                "--experimental", str(self.b)
            ]), 2)


if __name__ == "__main__":
    unittest.main()
