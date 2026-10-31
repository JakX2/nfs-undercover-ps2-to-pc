"""V28 conversion tests. Only locally generated synthetic EA MicroTalk frames."""
import io
import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import undercover_mt10_private_bridge_v28 as v28
from ea_mt10_synthetic_silence_v27 import build_pair
from schl_wrapper_audit_v25 import parse_stream,compare


class V28Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.original = self.home / "orig.asf"
        self.original.write_bytes(build_pair(pulse=True)[0])

    def test_rewrap_original_synthetic_mt10(self):
        raw = self.original.read_bytes()
        target, details = v28.convert(raw)
        self.assertEqual(details["source_header"]["platform"], 5)
        self.assertEqual(details["source_header"]["version"], 3)
        self.assertEqual(details["target_header"]["platform"], 0)
        self.assertEqual(details["target_header"]["version"], 2)
        self.assertEqual(details["target_header"]["codec2"], 4)
        self.assertEqual(details["target_header"]["rate"], 22050)
        self.assertEqual(details["target_header"]["sample_count"], 432)
        self.assertEqual(parse_stream(target)["total_scdl_samples"], 432)

    def test_unmodified_body_and_blocks(self):
        original = self.original.read_bytes()
        target, _ = v28.convert(original)
        orig_h = v28.parse_header(original)["header_size"]
        targ_h = v28.parse_header(target)["header_size"]
        self.assertEqual(original[orig_h:], target[targ_h:])
        other = self.home / "pc_style.asf"
        other.write_bytes(target)
        self.assertTrue(compare(self.original, other)["structurally_lossless_wrapper"])

    def test_source_not_changed(self):
        original = self.original.read_bytes()
        v28.convert(original)
        self.assertEqual(self.original.read_bytes(), original)

    def test_reject_pcm_codec2_zero(self):
        data = self.original.read_bytes().replace(b"\xA0\x01\x04", b"\xA0\x01\x00", 1)
        with self.assertRaises(v28.BridgeError):
            v28.convert(data)

    def test_reject_pc_source(self):
        with self.assertRaises(v28.BridgeError):
            v28.convert(build_pair(pulse=True)[1])

    def test_reject_sample_count_mismatch(self):
        data = self.original.read_bytes().replace(b"\x85\x02\x01\xB0", b"\x85\x02\x01\xB1", 1)
        self.assertNotEqual(data,self.original.read_bytes())
        with self.assertRaises(v28.BridgeError):
            v28.convert(data)

    def test_reject_stereo(self):
        data = self.original.read_bytes().replace(b"\x82\x01\x01", b"\x82\x01\x02", 1)
        with self.assertRaises(v28.BridgeError):
            v28.convert(data)

    def test_reject_unknown_header_patch(self):
        raw = bytearray(self.original.read_bytes())
        at = raw.find(b"\x80\x01\x03")
        self.assertGreater(at,0)
        raw[at] = 0xDE
        with self.assertRaises(v28.BridgeError):
            v28.convert(raw)

    def test_reject_missing_terminator(self):
        raw = bytearray(self.original.read_bytes())
        p = raw.find(b"\xFF",12,36)
        self.assertGreater(p,0)
        raw[p] = 0xDE
        with self.assertRaises(v28.BridgeError):
            v28.convert(raw)

    def test_explicit_rate_retained(self):
        raw = self.original.read_bytes()
        self.assertEqual(v28.parse_header(raw)["rate"], 22050)
        target,_ = v28.convert(raw)
        self.assertEqual(v28.parse_header(target)["rate"], 22050)

    def test_rate_implicit_22050(self):
        raw = self.original.read_bytes()
        # synthetic PS2 header has explicit rate; rebuild a valid header without patch 0x84
        h = v28.parse_header(raw)
        header = raw[:h["header_size"]]
        target_patch = b"\x84\x02\x56\x22"  # big-endian 22050
        self.assertIn(target_patch,header)
        header_data = header[8:].replace(target_patch, b"")
        header_data = header_data.rstrip(b"\x00")
        header_data += b"\x00" * (-len(header_data) % 4)
        new_header = b"SCHl" + struct.pack("<I",len(header_data)+8) + header_data
        changed = new_header + raw[h["header_size"]:]
        self.assertEqual(v28.parse_header(changed)["rate"], 22050)
        v28.convert(changed)

    def test_accept_priority_and_misc_patches(self):
        self.assertEqual(v28.parse_header(self.original.read_bytes())["channels"],1)

    def test_run_pair_without_decoder_keeps_no_audio(self):
        r=v28.run_pair(self.original)
        self.assertTrue(r["body_byte_identical"])
        self.assertIsNone(r["pcm_equivalent"])
        self.assertFalse(r["real_decoder_executed"])
        self.assertFalse(r["pc_shape_retained_locally"])
        self.assertFalse(r["carbon_pc_runtime_verified"])

    def test_retained_experimental_audio_is_explicit_opt_in(self):
        path=self.home/"keep.asf"
        r=v28.run_pair(self.original,retain=path)
        self.assertTrue(path.is_file())
        self.assertTrue(r["pc_shape_retained_locally"])

    def test_retained_audio_never_overwrites(self):
        path=self.home/"keep.asf"
        path.write_bytes(b"preserve")
        with self.assertRaises(FileExistsError):
            v28.run_pair(self.original,retain=path)
        self.assertEqual(path.read_bytes(),b"preserve")

    def test_cli_report_is_metadata_only(self):
        directory=self.home/"result"
        with patch("sys.stdout",new_callable=io.StringIO):
            rc=v28.main(["--original",str(self.original),"--out-dir",str(directory)])
        self.assertEqual(rc,0)
        self.assertEqual(sorted(x.name for x in directory.iterdir()),["report.json"])
        obj=json.loads((directory/"report.json").read_text())
        self.assertTrue(obj["body_byte_identical"])
        self.assertIsNone(obj["pcm_equivalent"])

    def test_cli_refuses_existing_folder(self):
        directory=self.home/"existing"
        directory.mkdir()
        with patch("sys.stderr",new_callable=io.StringIO):
            rc=v28.main(["--original",str(self.original),"--out-dir",str(directory)])
        self.assertEqual(rc,2)

    def test_cli_keep_pc_shape_private(self):
        directory=self.home/"result_kept"
        with patch("sys.stdout",new_callable=io.StringIO):
            rc=v28.main(["--original",str(self.original),"--out-dir",str(directory),"--keep-pc-shape"])
        self.assertEqual(rc,0)
        self.assertTrue((directory/"experimental_pc_style.asf").exists())

    def test_missing_source_rejected(self):
        with self.assertRaises(v28.BridgeError):
            v28.run_pair(self.home/"not-found.asf")

    def test_derived_header_different_from_original(self):
        orig=self.original.read_bytes()
        converted,details=v28.convert(orig)
        self.assertNotEqual(orig,converted)
        self.assertEqual(details["scdl_blocks"],1)
        self.assertEqual(details["compressed_body_sha256"],
                         parse_stream(orig)["post_header_sha256"])


if __name__=="__main__":
    unittest.main()
