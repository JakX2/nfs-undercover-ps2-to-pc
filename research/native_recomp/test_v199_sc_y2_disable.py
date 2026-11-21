#!/usr/bin/env python3
"""V199 original-free Wii second IOS Y2 timebase native continuation tests."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v198_sc_y2_time_harness import derive as previous,NEXT_END as PREVIOUS_END
from derive_v199_sc_y2_disable_harness import derive,STOP,CONTINUE,OBSERVER,NEXT_END
from derive_v199_sc_y2_disable_runner import derive as runner,PATTERN,PASS
HERE=Path(__file__).resolve().parent

class V199(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=previous(base)
        cls.after=derive(base)

    def test_authentic_timebase_returns_into_original_scheduler_disable(self):
        self.assertIn(STOP,self.before)
        self.assertNotIn(STOP,self.after)
        self.assertIn(CONTINUE,self.after)
        self.assertIn("addr==0x805293f8u",OBSERVER)
        self.assertIn("ctx.lr==0x80526c98u",OBSERVER)
        self.assertIn("ctx.inst_count>v199_time_inst",OBSERVER)
        self.assertIn("v196_resume==0x8052f830u",OBSERVER)
        self.assertIn(NEXT_END,self.after)
        self.assertNotIn(PREVIOUS_END,self.after)

    def test_no_guest_msr_software_irq_or_fake_completion(self):
        for tok in ("ipc70_bus.tick(", "scheduler.service_one(", "ctx.mmu.write32(",
                    "ipc70_bus.write32(", "ipc70_ram.write8("):
            self.assertEqual(self.before.count(tok),self.after.count(tok))
        for body in (CONTINUE,OBSERVER,NEXT_END):
            for tok in ("ipc70_bus.write","ipc70_ram.write","service_one(",
                        "ipc70_bus.tick(","ctx.mmu.write"):
                self.assertNotIn(tok,body)
        self.assertIn("queued_replies()==1u",OBSERVER)
        self.assertNotRegex(OBSERVER,r"\bctx\.(?:msr|gpr|pc|lr|srr0|srr1)\s*=(?!=)")
        with self.assertRaises(ValueError):
            derive("invalid")

    def test_private_runner_and_workflow_retain_sixteen_trial_gates(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        self.assertIn("derive_v199_sc_y2_disable_harness.py",script)
        self.assertIn("V198_SC_Y2_TIME verified=1",script)
        self.assertIn("V199_SC_Y2_DISABLE verified=1",script)
        good="V199_Y2_DISABLE route=1 masked=1 pending=1 progressed=1 resume=1 pc=805293f8 lr=80526c98"
        self.assertTrue(re.fullmatch(PASS,good))
        self.assertTrue(re.fullmatch(PATTERN,good.replace("route=1","route=0")))
        self.assertFalse(re.fullmatch(PASS,good.replace("masked=1","masked=0")))
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/"run.sh";f.write_text(script,encoding="utf-8")
            subprocess.run(["bash","-n",str(f)],check=True)
        wf=(HERE.parents[1]/".github/workflows/wii-v199-sc-y2-disable.yml").read_text()
        self.assertIn("run_v199_sc_y2_disable.sh",wf)
        self.assertIn("V199_SC_Y2_DISABLE verified=1",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)

if __name__=="__main__":
    unittest.main()
