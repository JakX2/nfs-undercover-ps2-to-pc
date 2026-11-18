#!/usr/bin/env python3
"""V86 original-free derivation and owner runner syntax regression."""
from pathlib import Path
import subprocess
import tempfile
import unittest
from derive_v85_both_stm_opens_harness import derive as previous
from derive_v86_stm_ioctl_harness import EDITS, derive
from derive_v86_stm_ioctl_runner import derive as runner
HERE=Path(__file__).resolve().parent
class AsyncSubmitTest(unittest.TestCase):
    def test_harness(self):
        base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text()
        prior=previous(base)
        s=derive(base)
        self.assertEqual(s,derive(base))
        for anchor,_ in EDITS:
            self.assertEqual(prior.count(anchor),1)
        for marker in ("V86_ASYNC_ENTRY","V86_ASYNC_SUBMIT","V86_TRIAL_PASS","POST_OWNER=0x805195ecu"):
            self.assertEqual(s.count(marker),1)
        for marker in ("V85_STM_OPENS","V84_SECOND_ACK","V82_RESUME_STATE","unexpected micro interpreter fallback",
                       "ctx.lr==0x8051a2bcu","I::EventHook"):
            self.assertIn(marker,s)
        self.assertEqual(s.count("ipc70_bus.reset()"),prior.count("ipc70_bus.reset()"))
        self.assertEqual(s.count("ctx.mmu.write"),prior.count("ctx.mmu.write"))
    def test_runner(self):
        s=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        self.assertIn("BOOT_PROGRESS entry=0x8000403C pc=0x805195EC stage=86",s)
        self.assertIn("V86_ASYNC_SUBMIT",s)
        self.assertIn("V85_STM_OPENS",s)
        self.assertIn("derive_v86_stm_ioctl_generator.py",s)
        self.assertLess(s.index("test_v77_continuous_ipc_ack_geometry.py"),s.index("restore_stm_ioctl_v86.py"))
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"run.sh";p.write_text(s)
            subprocess.run(["bash","-n",str(p)],check=True)
if __name__=="__main__":
    unittest.main()
