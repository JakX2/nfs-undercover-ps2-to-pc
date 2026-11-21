#!/usr/bin/env python3
"""V203 original-free second Y2 IPC repeated-read and distinct helper tests."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v202_sc_y2_next_harness import derive as previous,NEXT_END as PREVIOUS_END
from derive_v203_sc_y2_distinct_harness import derive,STOP,CONTINUE,OBSERVER,NEXT_END
from derive_v203_sc_y2_distinct_runner import derive as runner,PATTERN,PASS
HERE=Path(__file__).resolve().parent

class V203(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=previous(base)
        cls.after=derive(base)

    def test_bounded_guest_reads_to_distinct_handler_owned_helper(self):
        self.assertIn(STOP,self.before)
        self.assertNotIn(STOP,self.after)
        self.assertIn(CONTINUE,self.after)
        for token in ("v196_live","v202_next_seen==1u",
                      "v203_distinct_seen==0u","v202_next_pc==0x8051905cu",
                      "v202_next_lr==0x8051935cu","ctx.lr>=0x80519318u",
                      "ctx.lr<0x805194c4u","v203_extra_reads<=32u",
                      "ctx.inst_count>v203_start_inst",
                      "ctx.gpr[13]==v202_first_r13",
                      "queued_replies()==1u","v203_distinct_pc=addr"):
            self.assertIn(token,OBSERVER)
        self.assertIn(NEXT_END,self.after)
        self.assertNotIn(PREVIOUS_END,self.after)

    def test_no_forced_second_ack_or_guest_state(self):
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

    def test_owner_runner_and_cleanup_enforce_full_native_gate(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        self.assertIn("derive_v203_sc_y2_distinct_harness.py",script)
        self.assertIn("V202_SC_Y2_NEXT verified=1",script)
        self.assertIn("V203_SC_Y2_DISTINCT verified=1",script)
        self.assertIn(')" -eq 16',script)
        good="V203_Y2_DISTINCT first=1 caller=1 progressed=1 masked=1 queued=1 reads=3 pc=8051906c lr=80519380"
        self.assertIsNotNone(re.fullmatch(PASS,good))
        self.assertIsNotNone(re.fullmatch(PATTERN,good.replace("masked=1","masked=0")))
        self.assertIsNone(re.fullmatch(PASS,good.replace("caller=1","caller=0")))
        wf=(HERE.parents[1]/".github/workflows/wii-v203-sc-y2-distinct.yml").read_text()
        self.assertIn("run_v203_sc_y2_distinct.sh",wf)
        self.assertIn("test_v203_sc_y2_distinct.py",wf)
        self.assertIn("V203_SC_Y2_DISTINCT verified=1",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)
        with tempfile.TemporaryDirectory() as directory:
            file=Path(directory)/"runner.sh"
            file.write_text(script,encoding="utf-8")
            subprocess.run(["bash","-n",str(file)],check=True)
            entry=Path(directory)/"entry.sh"
            entry.write_text((HERE/"run_v203_sc_y2_distinct.sh").read_text(),encoding="utf-8")
            subprocess.run(["bash","-n",str(entry)],check=True)

if __name__=="__main__":
    unittest.main()
