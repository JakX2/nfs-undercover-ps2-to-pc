#!/usr/bin/env python3
"""V196 original-free second Y2 PowerPC exception vector continuation gates."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v195_sc_y2_irq_entry_harness import derive as previous,IRQ
from derive_v196_sc_y2_vector_harness import derive,OBSERVER,NEXT_TRIAL
from derive_v196_sc_y2_vector_runner import derive as runner,PATTERN,PASS
HERE=Path(__file__).resolve().parent

class V196(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=previous(base)
        cls.after=derive(base)

    def test_original_wii_second_y2_vector_runs_after_full_v195_proof(self):
        self.assertEqual(self.before.count(IRQ),1)
        self.assertIn(IRQ,self.after)
        self.assertEqual(self.after.count("V196_Y2_VECTOR vector="),1)
        self.assertEqual(self.after.count("v196_live&&addr==0x80000500u"),1)
        self.assertEqual(self.after.count("v196_live&&addr==0x80526ce0u"),1)
        self.assertIn("ctx.mmu.read32(frame+408u)==v196_resume",OBSERVER)
        self.assertIn("ctx.mmu.read32(frame+412u)==v196_srr1",OBSERVER)
        self.assertIn("ctx.mmu.read32(frame+140u)==v196_xer",OBSERVER)
        self.assertIn("ctx.inst_count>v196_start_inst",OBSERVER)
        self.assertIn("try{run_game(c);}catch(const ExceptionStop&)",NEXT_TRIAL)
        self.assertIn("nwii::runtime::v141_live=false;",NEXT_TRIAL)
        self.assertGreater(self.after.index(NEXT_TRIAL),self.after.index(IRQ))
        self.assertIn("c.srr0==0x8052f830u",NEXT_TRIAL)

    def test_no_guest_memory_or_ios_reply_fabrication(self):
        for token in ("ipc70_bus.tick(", "scheduler.service_one(", "ctx.mmu.write32(",
                      "ipc70_bus.write32(", "ipc70_ram.write8("):
            self.assertEqual(self.before.count(token),self.after.count(token),token)
        for part in (NEXT_TRIAL,OBSERVER):
            for forbidden in ("c.mmu.write","ctx.mmu.write","ipc70_ram.write",
                              "ipc70_bus.write","service_one(","ipc70_bus.tick("):
                self.assertNotIn(forbidden,part)
        self.assertNotRegex(NEXT_TRIAL,r"\bc\.(?:srr0|srr1|msr|lr|ctr|xer)\s*=(?!=)")
        self.assertNotRegex(OBSERVER,r"\bctx\.(?:srr0|srr1|msr|lr|ctr|xer)\s*=(?!=)")
        self.assertIn("v196_live=false;",self.after)
        with self.assertRaises(ValueError):
            derive("invalid")

    def test_owner_runner_preserves_all_prior_native_gates(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        self.assertIn("derive_v196_sc_y2_vector_harness.py",script)
        self.assertIn("V195_SC_Y2_VECTOR verified=1",script)
        self.assertIn("V196_SC_Y2_VECTOR verified=1",script)
        self.assertIn("V196_ENTRY_COUNT lines=$v196_count",script)
        self.assertIn('trap \'rm -rf -- "$work"\' EXIT',script)
        good="V196_Y2_VECTOR vector=1 handler=1 saved=1 pending=1 progressed=1 resume=8052f830 pc=80526ce0"
        self.assertTrue(re.fullmatch(PASS,good))
        self.assertTrue(re.fullmatch(PATTERN,good.replace("saved=1","saved=0")))
        self.assertFalse(re.fullmatch(PASS,good.replace("pending=1","pending=0")))
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/"run.sh";p.write_text(script,encoding="utf-8")
            subprocess.run(["bash","-n",str(p)],check=True)

    def test_owner_workflow_private_cleanup(self):
        wf=(HERE.parents[1]/".github/workflows/wii-v196-sc-y2-vector.yml").read_text()
        self.assertIn("run_v196_sc_y2_vector.sh",wf)
        self.assertIn("V196_SC_Y2_VECTOR verified=1",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)

if __name__=="__main__":
    unittest.main()
