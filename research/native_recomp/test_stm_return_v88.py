#!/usr/bin/env python3
"""V88 original-free active-thread IRQ derivation and runner guard."""
from pathlib import Path
import subprocess
import tempfile
import unittest
from derive_v87_stm_event_harness import derive as previous
from derive_v88_stm_return_harness import EDITS, derive
from derive_v88_stm_return_runner import derive as runner
HERE=Path(__file__).resolve().parent
class StmReturnTest(unittest.TestCase):
    def test_harness(self):
        base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text()
        prior=previous(base)
        s=derive(base)
        self.assertEqual(s,derive(base))
        for anchor,_ in EDITS:
            self.assertEqual(prior.count(anchor),1)
        for marker in ("V88_ACTIVE_VECTOR","V88_ACTIVE_ACK","V88_ACTIVE_RFI","V88_STM_RETURN","V88_TRIAL_PASS","POST_OWNER=0x80520968u"):
            self.assertEqual(s.count(marker),1)
        for marker in ("V87_DEFERRED","V86_ASYNC_SUBMIT","V85_STM_OPENS","V82_RESUME_STATE","unexpected micro interpreter fallback",
                       "ctx.gpr[4]==THREAD","ctx.srr0==async88_resume"):
            self.assertIn(marker,s)
        self.assertEqual(s.count("ipc70_bus.reset()"),prior.count("ipc70_bus.reset()"))
        self.assertEqual(s.count("ctx.mmu.write"),prior.count("ctx.mmu.write"))
    def test_runner(self):
        s=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        self.assertIn("BOOT_PROGRESS entry=0x8000403C pc=0x80520968 stage=88",s)
        self.assertIn("V88_STM_RETURN",s)
        self.assertIn("restore_stm_ioctl_v86.py",s)
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"run.sh";p.write_text(s)
            subprocess.run(["bash","-n",str(p)],check=True)
if __name__=="__main__":
    unittest.main()
