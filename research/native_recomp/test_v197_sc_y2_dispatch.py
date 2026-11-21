#!/usr/bin/env python3
"""V197 original-free verification of second Y2 handler to IRQ dispatcher."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v196_sc_y2_vector_harness import derive as previous
from derive_v197_sc_y2_dispatch_harness import (
    derive,STOP,CONTINUE,OBSERVER,PREVIOUS_END,NEW_END,
)
from derive_v197_sc_y2_dispatch_runner import derive as runner,PATTERN,PASS
HERE=Path(__file__).resolve().parent

class V197(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=previous(base)
        cls.after=derive(base)

    def test_real_handler_executes_until_original_dispatch(self):
        self.assertIn(STOP,self.before)
        self.assertNotIn(STOP,self.after)
        self.assertIn(CONTINUE,self.after)
        self.assertIn("addr==0x80526a3cu",OBSERVER)
        self.assertIn("ctx.mmu.read32(frame+408u)==v196_resume",OBSERVER)
        self.assertIn("ctx.mmu.read32(frame+412u)==v196_srr1",OBSERVER)
        self.assertIn("ctx.mmu.read32(frame+4u*i)==v196_gprs[i]",OBSERVER)
        self.assertIn("ctx.inst_count>v197_handler_inst",OBSERVER)
        self.assertIn(NEW_END,self.after)
        self.assertNotIn(PREVIOUS_END,self.after)
        self.assertIn("v197_dispatch_seen==1u",NEW_END)
        self.assertIn("c.pc==0x80526a3cu",NEW_END)

    def test_preserves_first_interrupt_and_second_ios_pending(self):
        for token in ("ipc70_bus.tick(", "scheduler.service_one(", "ctx.mmu.write32(",
                      "ipc70_bus.write32(", "ipc70_ram.write8("):
            self.assertEqual(self.before.count(token),self.after.count(token))
        for part in (CONTINUE,OBSERVER,NEW_END):
            for forbidden in ("ctx.mmu.write","ipc70_bus.write","ipc70_ram.write",
                              "service_one(","ipc70_bus.tick("):
                self.assertNotIn(forbidden,part)
        self.assertIn("queued_replies()==1u",OBSERVER)
        with self.assertRaises(ValueError):
            derive("invalid")

    def test_runner_owner_sixteen_trials_and_safety(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        self.assertIn("derive_v197_sc_y2_dispatch_harness.py",script)
        self.assertIn("V196_SC_Y2_VECTOR verified=1",script)
        self.assertIn("V197_SC_Y2_DISPATCH verified=1",script)
        self.assertIn("V197_ENTRY_COUNT lines=$v197_count",script)
        good="V197_Y2_DISPATCH route=1 regs=1 status=1 pending=1 progressed=1 resume=8052f830 pc=80526a3c"
        self.assertTrue(re.fullmatch(PASS,good))
        self.assertFalse(re.fullmatch(PASS,good.replace("regs=1","regs=0")))
        self.assertTrue(re.fullmatch(PATTERN,good.replace("regs=1","regs=0")))
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"run.sh";p.write_text(script)
            subprocess.run(["bash","-n",str(p)],check=True)

    def test_private_owner_workflow_cleans_all_originals(self):
        wf=(HERE.parents[1]/".github/workflows/wii-v197-sc-y2-dispatch.yml").read_text()
        self.assertIn("run_v197_sc_y2_dispatch.sh",wf)
        self.assertIn("V197_SC_Y2_DISPATCH verified=1",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)

if __name__=="__main__":
    unittest.main()
