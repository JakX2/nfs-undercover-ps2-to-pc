#!/usr/bin/env python3
"""Original-free V200 second Y2 IRQ handler selection regression tests."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v199_sc_y2_disable_harness import derive as previous,NEXT_END as PREVIOUS_END
from derive_v200_sc_y2_ipc_harness import derive,STOP,CONTINUE,OBSERVER,NEXT_END
from derive_v200_sc_y2_ipc_runner import derive as runner,PATTERN,PASS
HERE=Path(__file__).resolve().parent

class V200(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=previous(base)
        cls.after=derive(base)

    def test_second_interrupt_reaches_live_registered_slot_and_frame(self):
        self.assertIn(STOP,self.before)
        self.assertNotIn(STOP,self.after)
        self.assertIn(CONTINUE,self.after)
        for key in ("v196_live","v199_disable_seen==1u","v200_ipc_seen==0u",
                    "addr==0x80519318u","ctx.ctr==addr","ctx.gpr[3]==27u",
                    "IRQ_TABLE+27u*4u","frame+408u","frame+412u",
                    "frame+132u","frame+136u","frame+140u",
                    "v196_resume","v196_srr1","v196_lr","v196_ctr",
                    "v196_xer","queued_replies()==1u",
                    "!ipc70_bus.pending_native_ios_request()",
                    "ctx.inst_count>v200_disable_inst"):
            self.assertIn(key,OBSERVER)
        # Never disable historical NAND checks globally: only the second
        # authenticated scheduler's nested helpers may bypass the stale V98
        # idle-queue observer after checking live IRQ state.
        self.assertIn("(addr==INT_DISABLE||addr==INT_RESTORE)",OBSERVER)
        self.assertIn("ctx.lr>=0x805293f8u&&ctx.lr<0x80529434u",OBSERVER)
        self.assertIn("v196_live&&v199_disable_seen==1u&&v200_ipc_seen==0u",OBSERVER)
        self.assertIn("scheduler nested helper lost pending IOS state",OBSERVER)
        self.assertIn(NEXT_END,self.after)
        self.assertNotIn(PREVIOUS_END,self.after)

    def test_only_observes_state_and_fails_closed(self):
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

    def test_owner_native_runner_requires_all_sixteen_original_trials(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        self.assertIn("derive_v200_sc_y2_ipc_harness.py",script)
        self.assertIn("V199_SC_Y2_DISABLE verified=1",script)
        self.assertIn("V200_SC_Y2_IPC verified=1",script)
        self.assertIn(')" -eq 16',script)
        good=("V200_Y2_IPC dispatch=1 context=1 registered=1 masked=1 "
              "pending=1 progressed=1 resume=1 pc=80519318 lr=80526c9c")
        self.assertIsNotNone(re.fullmatch(PASS,good))
        self.assertIsNotNone(re.fullmatch(PATTERN,good.replace("context=1","context=0")))
        self.assertIsNone(re.fullmatch(PASS,good.replace("registered=1","registered=0")))
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"runner.sh"
            path.write_text(script,encoding="utf-8")
            subprocess.run(["bash","-n",str(path)],check=True)

    def test_public_private_isolation_and_workflow(self):
        workflow=(HERE.parents[1]/".github/workflows/wii-v200-sc-y2-ipc.yml").read_text()
        self.assertIn("run_v200_sc_y2_ipc.sh",workflow)
        self.assertIn("test_v200_sc_y2_ipc.py",workflow)
        self.assertIn("V200_SC_Y2_IPC verified=1",workflow)
        self.assertIn("V200_Y2_IPC dispatch=1 context=1 registered=1",workflow)
        self.assertEqual(workflow.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",workflow)
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"runner.sh"
            path.write_text((HERE/"run_v200_sc_y2_ipc.sh").read_text(),encoding="utf-8")
            subprocess.run(["bash","-n",str(path)],check=True)

if __name__=="__main__":
    unittest.main()
