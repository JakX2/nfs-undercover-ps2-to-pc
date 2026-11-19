#!/usr/bin/env python3
"""V109 original-free overlay and strict runner regression."""
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v108_sc_literal_restore_harness import derive as previous
from derive_v109_sc_nonempty_harness import derive,EDITS
from derive_v109_sc_nonempty_runner import derive as runner
HERE=Path(__file__).resolve().parent
class V109(unittest.TestCase):
    def test_overlay(self):
        base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text()
        old=previous(base);s=derive(base)
        for a,_ in EDITS:self.assertEqual(old.count(a),1,a[:80])
        self.assertEqual(s,derive(base))
        for key in ("V109_SC_SECOND_COPY","V109_SC_NEXT_LENGTH","V109_TRIAL_PASS",
                    "POST_OWNER=0x80544ac0u"):
            self.assertEqual(s.count(key),1,key)
        self.assertEqual(s.count("ctx.mmu.write"),old.count("ctx.mmu.write"))
        self.assertEqual(s.count("seed_stm_data("),old.count("seed_stm_data("))
        self.assertEqual(s.count("ipc70_bus.reset()"),old.count("ipc70_bus.reset()"))
    def test_runner(self):
        s=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for label in ("derive_v109_sc_nonempty_harness.py",
                      "V109_SC_SECOND_COPY input=1 bounded=1",
                      "V109_SC_NEXT_LENGTH route=1 data=1 prior=1",
                      "BOOT_PROGRESS entry=0x8000403C pc=0x80544AC0 stage=109"):
            self.assertIn(label,s)
        self.assertIn("derive_v108_sc_literal_restore_harness.py",str(
            (HERE/"derive_v108_sc_literal_runner.py").read_text()))
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/"run.sh";f.write_text(s)
            subprocess.run(["bash","-n",str(f)],check=True)
if __name__=="__main__":unittest.main()
