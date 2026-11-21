#!/usr/bin/env python3
"""V208 original-free scheduler guest successor checks."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v207_sc_y2_helper_next_harness import derive as previous, OBSERVER as PREVIOUS_OBSERVER, NEXT_END as PREVIOUS_END
from derive_v208_sc_y2_scheduler_next_harness import derive, STOP, CONTINUE, OBSERVER, NEXT_END
from derive_v208_sc_y2_scheduler_next_runner import derive as runner, PATTERN, PASS
from derive_v185_sc_reply_next_harness import OBSERVER_HEADER
HERE=Path(__file__).resolve().parent

class V208(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=previous(base)
        cls.after=derive(base)

    def test_original_scheduler_executes_only_from_verified_v207(self):
        self.assertIn(STOP,PREVIOUS_OBSERVER)
        self.assertNotIn(STOP,self.after)
        self.assertIn(CONTINUE,self.after)
        self.assertIn(OBSERVER_HEADER+"\n"+OBSERVER,self.after)
        self.assertIn(NEXT_END,self.after)
        self.assertNotIn(PREVIOUS_END,self.after)
        for m in ("addr==0x80529434u&&ctx.lr==0x80526cb0u",
                  "v196_live&&v207_next_seen==1u&&v208_next_seen==0u",
                  "ctx.inst_count>v208_start_inst","queued_replies()<=1u",
                  "IOS::Open","IOS::Reply","ctx.gpr[13]==v147_first_r13",
                  "v208_target_pc=addr;v208_target_lr=ctx.lr"):
            self.assertIn(m,CONTINUE+OBSERVER)

    def test_no_cpu_state_or_ios_synthesis(self):
        for token in ("ipc70_bus.tick(", "scheduler.service_one(", "ctx.mmu.write32(",
                      "ipc70_bus.write32(", "ipc70_ram.write8("):
            self.assertEqual(self.before.count(token),self.after.count(token))
        for part in (CONTINUE,OBSERVER,NEXT_END):
            for token in ("ipc70_bus.write","ipc70_ram.write","service_one(",
                          "ipc70_bus.tick(","ctx.mmu.write"):
                self.assertNotIn(token,part)
        self.assertNotRegex(OBSERVER,r"\bctx\.(?:msr|pc|lr|srr0|srr1)\s*=(?!=)")
        with self.assertRaises(ValueError):
            derive("invalid")

    def test_sixteen_trial_owner_gate_and_cleanup(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        self.assertIn("derive_v208_sc_y2_scheduler_next_harness.py",script)
        self.assertIn("V207_SC_Y2_HELPER_NEXT verified=1",script)
        self.assertIn("V208_SC_Y2_SCHED_NEXT verified=1",script)
        good="V208_Y2_SCHED y2=1 irq_down=1 queue=1 open=1 replied=0 guest=1 caller=1 coherent=1 mapped=1 sc=1 ee=0 pc=805293f8 lr=80529450"
        self.assertIsNotNone(re.fullmatch(PASS,good))
        self.assertIsNotNone(re.fullmatch(PATTERN,good.replace("guest=1","guest=0")))
        self.assertIsNone(re.fullmatch(PASS,good.replace("mapped=1","mapped=0")))
        wf=(HERE.parents[1]/".github/workflows/wii-v208-sc-y2-scheduler-next.yml").read_text()
        self.assertIn("run_v208_sc_y2_scheduler_next.sh",wf)
        self.assertIn("test_v208_sc_y2_scheduler_next.py",wf)
        self.assertIn("V208_SC_Y2_SCHED_NEXT verified=1",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"runner.sh";p.write_text(script)
            subprocess.run(["bash","-n",str(p)],check=True)
            p=Path(d)/"entry.sh";p.write_text((HERE/"run_v208_sc_y2_scheduler_next.sh").read_text())
            subprocess.run(["bash","-n",str(p)],check=True)

if __name__=="__main__":
    unittest.main()
