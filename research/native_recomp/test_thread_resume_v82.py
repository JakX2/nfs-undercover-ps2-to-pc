#!/usr/bin/env python3
"""V82 original-free overlay and runner regression."""
from pathlib import Path
import subprocess
import tempfile
import unittest
from derive_v81_ready_thread_harness import derive as previous
from derive_v82_thread_resume_harness import derive, EDITS
from derive_v82_thread_resume_runner import derive as runner
HERE = Path(__file__).resolve().parent
class ResumeThreadTest(unittest.TestCase):
    def test_overlay(self):
        base = (HERE / "test_start_to_ipc_ack_v77.cpp").read_text()
        source = derive(base)
        self.assertEqual(source, derive(base))
        for marker in ("V82_REPLY_RETURN", "V82_LOAD_CONTEXT", "V82_RESUME_STATE",
                       "V82_TRIAL_PASS", "POST_OWNER=0x805265d4u"):
            self.assertEqual(source.count(marker), 1)
        for marker in ("V81_READY_STATE", "V80_WAKE_ENTRY", "V79_RFI_STATE",
                       "unexpected micro interpreter fallback"):
            self.assertIn(marker, source)
        prev = previous(base)
        for old, new in EDITS:
            self.assertEqual(prev.count(old), 1)
        self.assertNotIn("ctx.mmu.write32(sleep73_queue", source)
    def test_runner(self):
        source = runner((HERE / "run_v79_continuous_reply_entry.sh").read_text())
        self.assertIn("BOOT_PROGRESS entry=0x8000403C pc=0x805265D4 stage=82", source)
        self.assertIn("V82_RESUME_STATE", source)
        self.assertIn("V81_READY_STATE", source)
        self.assertIn("derive_v82_thread_resume_harness.py", source)
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "run.sh"
            p.write_text(source)
            subprocess.run(["bash", "-n", str(p)], check=True)
if __name__ == "__main__":
    unittest.main()
