#!/usr/bin/env python3
"""V98 original-free exact overlay checks."""
import unittest
import subprocess
import tempfile
from pathlib import Path
from derive_v97_es_close_harness import derive as previous
from derive_v98_nand_registration_harness import EDITS, derive
from derive_v98_nand_registration_runner import derive as runner
HERE=Path(__file__).resolve().parent
class NandRegistrationTest(unittest.TestCase):
    def test_harness(self):
        base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text()
        prior=previous(base);s=derive(base)
        for a,_ in EDITS:self.assertEqual(prior.count(a),1)
        self.assertEqual(s,derive(base))
        for marker in ("V98_NAND_CALLBACK","V98_TRIAL_PASS","POST_OWNER=0x8051e5bcu"):
            self.assertEqual(s.count(marker),1)
        self.assertEqual(s.count("ctx.mmu.write"),prior.count("ctx.mmu.write"))
        self.assertEqual(s.count("ipc70_bus.reset()"),prior.count("ipc70_bus.reset()"))
        self.assertIn('seed_stm_data(ctx,post98_node,8u)',s)
    def test_runner(self):
        s=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        self.assertIn("BOOT_PROGRESS entry=0x8000403C pc=0x8051E5BC stage=98",s)
        self.assertIn("restore_es_close_v97.py",s)
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"run.sh";p.write_text(s)
            subprocess.run(["bash","-n",str(p)],check=True)
if __name__=="__main__":unittest.main()
