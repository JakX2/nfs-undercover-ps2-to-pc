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

class ReplyWakeOverlayTest(unittest.TestCase):
    def setUp(self):
        self.source = BASE.read_text(encoding="utf-8")

    def test_wake_overlay_preserves_original_reply_entry(self):
        from derive_v80_reply_wake_harness import derive as derive_wake
        result = derive_wake(self.source)
        self.assertEqual(result, derive_wake(self.source))
        for marker in ("V79_RFI_STATE", "V79_REPLY_ENTRY", "V80_WAKE_ENTRY",
                       "V80_TRIAL_PASS", "POST_OWNER=0x8052a51cu"):
            self.assertEqual(result.count(marker), 1)
        self.assertIn("ctx.gpr[3]==sleep73_queue", result)
        self.assertIn("ctx.guest_data_invalidate_count>wake80_invalidate_before", result)
        self.assertIn("unexpected micro interpreter fallback", result)
        self.assertIn("IPC initial SDA fixture word unexpectedly populated", result)

    def test_wake_output_refuses_overwrite(self):
        from derive_v80_reply_wake_harness import derive as derive_wake
        with tempfile.TemporaryDirectory() as directory:
            d = Path(directory)
            src, dst = d / "base.cpp", d / "wake.cpp"
            src.write_text(self.source, encoding="utf-8")
            command = [sys.executable, str(HERE / "derive_v80_reply_wake_harness.py"),
                       str(src), str(dst)]
            self.assertEqual(subprocess.run(command, capture_output=True).returncode, 0)
            self.assertEqual(dst.read_text(encoding="utf-8"), derive_wake(self.source))
            dst.write_text("sentinel", encoding="utf-8")
            self.assertNotEqual(subprocess.run(command, capture_output=True).returncode, 0)
            self.assertEqual(dst.read_text(encoding="utf-8"), "sentinel")


class ReplyBuildDerivationTest(unittest.TestCase):
    def test_generator_separates_authenticated_roots(self):
        from derive_v79_reply_generator import EDITS as generator_edits, derive
        source = (HERE / "generate_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        result = derive(source)
        self.assertIn("0x80529940u,0x80529718u,0x805229b4u", result)
        self.assertIn("V79 authenticated reschedule tail missing", result)
        self.assertIn("V79 original context load RFI missing", result)
        for anchor, _ in generator_edits:
            with self.assertRaises(ValueError):
                derive(source.replace(anchor, "", 1))

    def test_wake_runner_derivation_shell_syntax(self):
        from derive_v80_reply_wake_runner import derive
        source = (HERE / "run_v79_continuous_reply_entry.sh").read_text(encoding="utf-8")
        result = derive(source)
        self.assertEqual(result.count("BOOT_PROGRESS entry=0x8000403C pc=0x8052A51C stage=80"), 1)
        self.assertNotIn("stage=79", result)
        self.assertIn("derive_v80_reply_wake_harness.py", result)
        self.assertIn("derive_v79_reply_generator.py", result)
        self.assertIn("V80_WAKE_ENTRY", result)
        self.assertIn("V79_RFI_STATE", result)
        with tempfile.TemporaryDirectory() as directory:
            script = Path(directory) / "run.sh"
            script.write_text(result, encoding="utf-8")
            self.assertEqual(subprocess.run(["bash", "-n", str(script)],
                                            capture_output=True).returncode, 0)


if __name__ == "__main__":
    unittest.main()
