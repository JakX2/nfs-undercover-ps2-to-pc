#!/usr/bin/env python3
"""Original-free V79 overlay guards, including no overwrite on failure."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from derive_v79_reply_harness import EDITS, derive

HERE = Path(__file__).resolve().parent
BASE = HERE / "test_start_to_ipc_ack_v77.cpp"

class ReplyOverlayTest(unittest.TestCase):
    def setUp(self):
        self.source = BASE.read_text(encoding="utf-8")

    def test_deterministic_complete(self):
        result = derive(self.source)
        self.assertEqual(result, derive(self.source))
        for marker in ("V79_RFI_STATE", "V79_REPLY_ENTRY", "V79_TRIAL_PASS",
                       "POST_OWNER=0x805190c0u"):
            self.assertEqual(result.count(marker), 1)
        self.assertIn("V77_ACK_STATE", result)
        self.assertIn("IPC initial SDA fixture word unexpectedly populated", result)
        self.assertIn("unexpected micro interpreter fallback", result)
        self.assertIn("ctx.gpr==vector75_gprs", result)

    def test_each_anchor_removal_fails(self):
        for i, (anchor, _) in enumerate(EDITS):
            with self.subTest(anchor=i):
                self.assertEqual(self.source.count(anchor), 1)
                with self.assertRaises(ValueError):
                    derive(self.source.replace(anchor, "/* removed anchor */", 1))

    def test_each_anchor_duplication_fails(self):
        for i, (anchor, _) in enumerate(EDITS):
            with self.subTest(anchor=i):
                with self.assertRaises(ValueError):
                    derive(self.source.replace(anchor, anchor + "\n" + anchor, 1))

    def test_output_atomic_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            d = Path(directory)
            source = d / "base.cpp"
            output = d / "derived.cpp"
            source.write_text("invalid input", encoding="utf-8")
            command = [sys.executable, str(HERE / "derive_v79_reply_harness.py"),
                       str(source), str(output)]
            self.assertNotEqual(subprocess.run(command, capture_output=True).returncode, 0)
            self.assertFalse(output.exists())
            source.write_text(self.source, encoding="utf-8")
            self.assertEqual(subprocess.run(command, capture_output=True).returncode, 0)
            self.assertEqual(output.read_text(encoding="utf-8"), derive(self.source))
            output.write_text("sentinel", encoding="utf-8")
            self.assertNotEqual(subprocess.run(command, capture_output=True).returncode, 0)
            self.assertEqual(output.read_text(encoding="utf-8"), "sentinel")

if __name__ == "__main__":
    unittest.main()
