#!/usr/bin/env python3
"""Source-only guard for dual original STM transaction derivation."""
from pathlib import Path
import subprocess
import tempfile
import unittest
from derive_v84_second_ack_harness import derive as previous
from derive_v85_both_stm_opens_harness import EDITS, derive
from derive_v85_both_stm_opens_runner import derive as runner
HERE=Path(__file__).resolve().parent
class BothOpensTest(unittest.TestCase):
    def test_harness(self):
        base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text()
        prior=previous(base)
        s=derive(base)
        self.assertEqual(s,derive(base))
        for anchor,_ in EDITS:
            self.assertEqual(prior.count(anchor),1)
        for marker in ("V85_STM_OPENS","V85_TRIAL_PASS","POST_OWNER=0x805265acu"):
            self.assertEqual(s.count(marker),1)
        for marker in ("V84_SECOND_ACK","V83_SECOND_OPEN","V82_RESUME_STATE","V79_RFI_STATE","unexpected micro interpreter fallback",
                       "ctx.pc==0x8052a430u","ctx.lr==0x8052b0d4u"):
            self.assertIn(marker,s)
        self.assertEqual(s.count("ipc70_ram.read32(submit72_phys+4u)==(open84_active?1u:0u)"),4)
        self.assertEqual(s.count("ipc70_bus.reset()"),prior.count("ipc70_bus.reset()"))
        self.assertEqual(s.count("ctx.mmu.write"),prior.count("ctx.mmu.write"))
    def test_runner(self):
        s=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        self.assertIn("BOOT_PROGRESS entry=0x8000403C pc=0x805265AC stage=85",s)
        self.assertIn("V85_STM_OPENS",s)
        self.assertIn("V84_SECOND_ACK",s)
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"run.sh";p.write_text(s)
            subprocess.run(["bash","-n",str(p)],check=True)
if __name__=="__main__":
    unittest.main()
