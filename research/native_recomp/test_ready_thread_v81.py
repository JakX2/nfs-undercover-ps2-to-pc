#!/usr/bin/env python3
"""V81 original-free overlay and runner regression."""
from pathlib import Path
import subprocess
import tempfile
import unittest
from derive_v80_reply_wake_harness import derive as previous
from derive_v81_ready_thread_harness import derive, EDITS
from derive_v81_ready_thread_runner import derive as runner
HERE = Path(__file__).resolve().parent
class ReadyThreadTest(unittest.TestCase):
    def test_overlay(self):
        base = (HERE / "test_start_to_ipc_ack_v77.cpp").read_text()
        source = derive(base)
        self.assertEqual(source, derive(base))
        for marker in ("V81_READY_STATE", "V81_TRIAL_PASS", "POST_OWNER=0x80529718u"):
            self.assertEqual(source.count(marker), 1)
        self.assertIn("V80_WAKE_ENTRY", source)
        self.assertIn("V79_RFI_STATE", source)
        self.assertIn("unexpected micro interpreter fallback", source)
        prev = previous(base)
        for old, new in EDITS:
            self.assertEqual(prev.count(old), 1)
        self.assertNotIn("ctx.mmu.write32(sleep73_queue", source)
    def test_runner(self):
        source = runner((HERE / "run_v79_continuous_reply_entry.sh").read_text())
        self.assertIn("BOOT_PROGRESS entry=0x8000403C pc=0x80529718 stage=81", source)
        self.assertIn("V81_READY_STATE", source)
        self.assertIn("V80_WAKE_ENTRY", source)
        self.assertIn("derive_v81_ready_thread_harness.py", source)
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "run.sh"
            p.write_text(source)
            subprocess.run(["bash", "-n", str(p)], check=True)
if __name__ == "__main__":
    unittest.main()
