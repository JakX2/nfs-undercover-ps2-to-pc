#!/usr/bin/env python3
"""V198 original-free second IOS Y2 IRQ timebase dispatch tests."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v197_sc_y2_dispatch_harness import derive as previous,NEW_END
from derive_v198_sc_y2_time_harness import derive,STOP,CONTINUE,OBSERVER,NEXT_END
from derive_v198_sc_y2_time_runner import derive as runner,PATTERN,PASS
HERE=Path(__file__).resolve().parent

class V198(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=previous(base)
        cls.after=derive(base)

    def test_second_irq_dispatcher_calls_actual_native_timebase(self):
        self.assertIn(STOP,self.before)
        self.assertNotIn(STOP,self.after)
        self.assertIn(CONTINUE,self.after)
        self.assertIn("addr==0x8052a824u",OBSERVER)
        self.assertIn("ctx.lr==0x80526c84u",OBSERVER)
        self.assertIn("ctx.inst_count>v198_dispatch_inst",OBSERVER)
        self.assertIn("v196_resume==0x8052f830u",OBSERVER)
        self.assertIn("v196_srr1!=0u&&v197_dispatch_seen==1u",OBSERVER)
        self.assertNotIn("ctx.srr0==v196_resume",OBSERVER)
        self.assertIn("ctx.mmu.read32(frame+408u)==v196_resume",self.before)
        self.assertIn("ctx.mmu.read32(frame+412u)==v196_srr1",self.before)
        self.assertIn(NEXT_END,self.after)
        self.assertNotIn(NEW_END,self.after)
        self.assertIn("v198_time_seen==1u",NEXT_END)
        self.assertIn("c.pc==0x8052a824u",NEXT_END)

    def test_only_original_guest_execution_no_fake_ios_or_msr(self):
        for tok in ("ipc70_bus.tick(", "scheduler.service_one(", "ctx.mmu.write32(",
                    "ipc70_bus.write32(", "ipc70_ram.write8("):
            self.assertEqual(self.before.count(tok),self.after.count(tok))
        for part in (CONTINUE,OBSERVER,NEXT_END):
            for tok in ("ipc70_bus.write","ipc70_ram.write","service_one(",
                        "ipc70_bus.tick(","ctx.mmu.write"):
                self.assertNotIn(tok,part)
        self.assertNotRegex(OBSERVER,r"\bctx\.(?:msr|gpr|pc|lr|srr0|srr1)\s*=(?!=)")
        self.assertIn("queued_replies()==1u",OBSERVER)
        with self.assertRaises(ValueError):
            derive("invalid")

    def test_safe_private_runner_gates_all_sixteen_owner_trials(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        self.assertIn("derive_v198_sc_y2_time_harness.py",script)
        self.assertIn("V197_SC_Y2_DISPATCH verified=1",script)
        self.assertIn("V198_SC_Y2_TIME verified=1",script)
        self.assertIn("V198_ENTRY_COUNT lines=$v198_count",script)
        good="V198_Y2_TIME time=1 masked=1 pending=1 progressed=1 resume=1 pc=8052a824 lr=80526c84"
        self.assertTrue(re.fullmatch(PASS,good))
        self.assertTrue(re.fullmatch(PATTERN,good.replace("time=1","time=0")))
        self.assertFalse(re.fullmatch(PASS,good.replace("pending=1","pending=0")))
        with tempfile.TemporaryDirectory() as folder:
            f=Path(folder)/"run.sh";f.write_text(script,encoding="utf-8")
            subprocess.run(["bash","-n",str(f)],check=True)

    def test_owner_workflow_cleans_originals_and_generated_cpp(self):
        wf=(HERE.parents[1]/".github/workflows/wii-v198-sc-y2-time.yml").read_text()
        self.assertIn("run_v198_sc_y2_time.sh",wf)
        self.assertIn("V198_SC_Y2_TIME verified=1",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)

if __name__=="__main__":
    unittest.main()
