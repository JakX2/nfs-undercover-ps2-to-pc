#!/usr/bin/env python3
"""V202 original-free second Y2 IPC read-helper successor regression tests."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v201_sc_y2_leaf_harness import derive as previous,NEXT_END as PREVIOUS_END
from derive_v202_sc_y2_next_harness import derive,STOP,CONTINUE,OBSERVER,NEXT_END
from derive_v202_sc_y2_next_runner import derive as runner,PATTERN,PASS
HERE=Path(__file__).resolve().parent

class V202(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=previous(base)
        cls.after=derive(base)

    def test_authentic_first_helper_returns_to_original_ipc_handler(self):
        self.assertIn(STOP,self.before)
        self.assertNotIn(STOP,self.after)
        self.assertIn(CONTINUE,self.after)
        for token in ("v196_live","v201_leaf_seen==1u","v202_next_seen==0u",
                      "v202_first_pc==0x8051905cu","v202_first_lr==0x8051933cu",
                      "ctx.lr>=0x80519318u","ctx.lr<0x805194c4u",
                      "ctx.inst_count>v202_first_inst",
                      "ctx.gpr[13]==v202_first_r13",
                      "queued_replies()==1u","v202_next_pc=addr"):
            self.assertIn(token,OBSERVER)
        self.assertIn(NEXT_END,self.after)
        self.assertNotIn(PREVIOUS_END,self.after)

    def test_does_not_fake_ios_or_cpu_state(self):
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

    def test_private_runner_sixteen_trial_gate_and_public_workflow(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        self.assertIn("derive_v202_sc_y2_next_harness.py",script)
        self.assertIn("V201_SC_Y2_LEAF verified=1",script)
        self.assertIn("V202_SC_Y2_NEXT verified=1",script)
        self.assertIn(')" -eq 16',script)
        good="V202_Y2_NEXT first=1 caller=1 stepped=1 masked=1 queued=1 pc=8051905c lr=8051934c"
        self.assertIsNotNone(re.fullmatch(PASS,good))
        self.assertIsNotNone(re.fullmatch(PATTERN,good.replace("caller=1","caller=0")))
        self.assertIsNone(re.fullmatch(PASS,good.replace("stepped=1","stepped=0")))
        workflow=(HERE.parents[1]/".github/workflows/wii-v202-sc-y2-next.yml").read_text()
        self.assertIn("run_v202_sc_y2_next.sh",workflow)
        self.assertIn("test_v202_sc_y2_next.py",workflow)
        self.assertIn("V202_SC_Y2_NEXT verified=1",workflow)
        self.assertEqual(workflow.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",workflow)
        with tempfile.TemporaryDirectory() as directory:
            f=Path(directory)/"runner.sh";f.write_text(script,encoding="utf-8")
            subprocess.run(["bash","-n",str(f)],check=True)
            entry=Path(directory)/"entry.sh"
            entry.write_text((HERE/"run_v202_sc_y2_next.sh").read_text(),encoding="utf-8")
            subprocess.run(["bash","-n",str(entry)],check=True)

if __name__=="__main__":
    unittest.main()
