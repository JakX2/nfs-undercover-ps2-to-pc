#!/usr/bin/env python3
"""V207 original-free bounded post-ACK successor tests."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v206_sc_y2_post_flag_harness import derive as previous, OBSERVER as PREVIOUS_OBSERVER, NEXT_END as PREVIOUS_END
from derive_v207_sc_y2_helper_next_harness import derive, STOP, CONTINUE, OBSERVER, NEXT_END
from derive_v207_sc_y2_helper_next_runner import derive as runner, PATTERN, PASS
from derive_v185_sc_reply_next_harness import OBSERVER_HEADER
HERE=Path(__file__).resolve().parent

class V207(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=previous(base)
        cls.after=derive(base)

    def test_resume_exact_owner_original_post_flag_call(self):
        self.assertIn(STOP,PREVIOUS_OBSERVER)
        self.assertNotIn(STOP,self.after)
        self.assertIn(CONTINUE,self.after)
        self.assertIn(OBSERVER_HEADER+"\n"+OBSERVER,self.after)
        self.assertIn(NEXT_END,self.after)
        self.assertNotIn(PREVIOUS_END,self.after)
        for marker in ("addr==0x8051b060u&&ctx.lr==0x805193a4u",
                       "v196_live&&v206_post_seen==1u&&v207_next_seen==0u",
                       "ctx.inst_count>v207_start_inst","queued_replies()<=1u",
                       "IOS::Open","IOS::Reply","read8(sc_addr)",
                       "v207_next_pc=addr;v207_next_lr=ctx.lr"):
            self.assertIn(marker, CONTINUE+OBSERVER)

    def test_hooks_are_read_only_and_fail_closed(self):
        for token in ("ipc70_bus.tick(", "scheduler.service_one(", "ctx.mmu.write32(",
                      "ipc70_bus.write32(", "ipc70_ram.write8("):
            self.assertEqual(self.before.count(token),self.after.count(token))
        for part in (CONTINUE,OBSERVER,NEXT_END):
            for bad in ("ipc70_bus.write", "ipc70_ram.write","service_one(",
                        "ipc70_bus.tick(","ctx.mmu.write"):
                self.assertNotIn(bad,part)
        self.assertNotRegex(OBSERVER,r"\bctx\.(?:msr|pc|lr|srr0|srr1)\s*=(?!=)")
        with self.assertRaises(ValueError):
            derive("missing")

    def test_owner_gate_sixteen_trials_and_cleanup(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        self.assertIn("derive_v207_sc_y2_helper_next_harness.py",script)
        self.assertIn("V206_SC_Y2_POST_FLAG verified=1",script)
        self.assertIn("V207_SC_Y2_HELPER_NEXT verified=1",script)
        good="V207_Y2_NEXT ack=1 irq_down=1 queued=1 open=1 replied=0 guest=1 caller=1 coherent=1 irqflag=1 mapped=1 sc=1 ee=0 pc=80529434 lr=805193a4"
        self.assertIsNotNone(re.fullmatch(PASS,good))
        self.assertIsNotNone(re.fullmatch(PATTERN,good.replace("guest=1","guest=0")))
        self.assertIsNone(re.fullmatch(PASS,good.replace("coherent=1","coherent=0")))
        wf=(HERE.parents[1]/".github/workflows/wii-v207-sc-y2-helper-next.yml").read_text()
        self.assertIn("run_v207_sc_y2_helper_next.sh",wf)
        self.assertIn("test_v207_sc_y2_helper_next.py",wf)
        self.assertIn("V207_SC_Y2_HELPER_NEXT verified=1",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"runner.sh"
            path.write_text(script,encoding="utf-8")
            subprocess.run(["bash","-n",str(path)],check=True)
            path=Path(d)/"entry.sh"
            path.write_text((HERE/"run_v207_sc_y2_helper_next.sh").read_text())
            subprocess.run(["bash","-n",str(path)],check=True)

if __name__=="__main__":
    unittest.main()
