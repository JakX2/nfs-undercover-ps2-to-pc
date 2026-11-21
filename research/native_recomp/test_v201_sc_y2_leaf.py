#!/usr/bin/env python3
"""V201 original-free second IOS Y2 IPC first native helper tests."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v200_sc_y2_ipc_harness import derive as previous,NEXT_END as PREVIOUS_END
from derive_v201_sc_y2_leaf_harness import derive,STOP,CONTINUE,OBSERVER,NEXT_END
from derive_v201_sc_y2_leaf_runner import derive as runner,PATTERN,PASS
HERE=Path(__file__).resolve().parent

class V201(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=previous(base)
        cls.after=derive(base)

    def test_authentic_second_irq_handler_executes_until_first_helper(self):
        self.assertIn(STOP,self.before)
        self.assertNotIn(STOP,self.after)
        self.assertIn(CONTINUE,self.after)
        for marker in ("v196_live","v200_ipc_seen==1u","v201_leaf_seen==0u",
                       "addr==0x8051905cu","addr==0x8051906cu",
                       "addr==0x8051b060u","ctx.lr>=0x80519318u",
                       "ctx.lr<0x805194c4u","queued_replies()==1u",
                       "!ipc70_bus.pending_native_ios_request()",
                       "ctx.inst_count>v201_ipc_inst","v196_resume==0x8052f830u",
                       "v201_leaf_pc=addr;v201_leaf_lr=ctx.lr"):
            self.assertIn(marker,OBSERVER)
        self.assertIn(NEXT_END,self.after)
        self.assertNotIn(PREVIOUS_END,self.after)

    def test_read_only_and_phase_scoped(self):
        for token in ("ipc70_bus.tick(", "scheduler.service_one(", "ctx.mmu.write32(",
                      "ipc70_bus.write32(", "ipc70_ram.write8("):
            self.assertEqual(self.before.count(token),self.after.count(token))
        for snippet in (CONTINUE,OBSERVER,NEXT_END):
            for forbidden in ("ipc70_bus.write","ipc70_ram.write","service_one(",
                              "ipc70_bus.tick(","ctx.mmu.write"):
                self.assertNotIn(forbidden,snippet)
        self.assertNotRegex(OBSERVER,r"\bctx\.(?:msr|gpr|pc|lr|srr0|srr1)\s*=(?!=)")
        with self.assertRaises(ValueError):
            derive("invalid")

    def test_original_owner_runner_requires_all_sixteen_trials(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        self.assertIn("derive_v201_sc_y2_leaf_harness.py",script)
        self.assertIn("V200_SC_Y2_IPC verified=1",script)
        self.assertIn("V201_SC_Y2_LEAF verified=1",script)
        self.assertIn(')" -eq 16',script)
        good="V201_Y2_LEAF call=1 masked=1 queued=1 stepped=1 prior=1 pc=8051905c lr=80519364"
        self.assertIsNotNone(re.fullmatch(PASS,good))
        self.assertIsNotNone(re.fullmatch(PATTERN,good.replace("call=1","call=0")))
        self.assertIsNone(re.fullmatch(PASS,good.replace("queued=1","queued=0")))
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"runner.sh"
            path.write_text(script,encoding="utf-8")
            subprocess.run(["bash","-n",str(path)],check=True)

    def test_workflow_enforces_owner_private_separation(self):
        workflow=(HERE.parents[1]/".github/workflows/wii-v201-sc-y2-leaf.yml").read_text()
        self.assertIn("run_v201_sc_y2_leaf.sh",workflow)
        self.assertIn("test_v201_sc_y2_leaf.py",workflow)
        self.assertIn("V201_SC_Y2_LEAF verified=1",workflow)
        self.assertEqual(workflow.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",workflow)
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"entry.sh"
            path.write_text((HERE/"run_v201_sc_y2_leaf.sh").read_text(),encoding="utf-8")
            subprocess.run(["bash","-n",str(path)],check=True)

if __name__=="__main__":
    unittest.main()
