#!/usr/bin/env python3
"""V206 original-free post-Hollywood-ACK native successor checks."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v205_sc_y2_flag_harness import (
    derive as previous, OBSERVER as PREVIOUS_OBSERVER, NEXT_END as PREVIOUS_END,
)
from derive_v206_sc_y2_post_flag_harness import derive, STOP, CONTINUE, OBSERVER, NEXT_END
from derive_v206_sc_y2_post_flag_runner import derive as runner, PATTERN, PASS
from derive_v185_sc_reply_next_harness import OBSERVER_HEADER
HERE=Path(__file__).resolve().parent

class V206(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=previous(base)
        cls.after=derive(base)

    def test_original_flag_ack_continues_into_real_guest_call(self):
        self.assertEqual(PREVIOUS_OBSERVER.count(STOP),1)
        self.assertNotIn(STOP,self.after)
        self.assertIn(CONTINUE,self.after)
        for marker in (
            "v196_live&&v205_flag_seen==1u&&v206_next_seen==0u",
            "ctx.pc==addr", "ctx.inst_count>v206_after_flag_inst",
            "((*ctrl&M::Y2)==0u)","((*flag&H::IPC_PPC)==0u)",
            "!ipc70_bus.external_irq_level()", "queued_replies()==1u",
            "ctx.gpr[13]==v202_first_r13", "read8(sc_addr)==1u",
            "v206_next_pc=addr;v206_next_lr=ctx.lr"):
            self.assertIn(marker,OBSERVER)
        self.assertIn(OBSERVER_HEADER+"\n"+OBSERVER,self.after)
        self.assertIn(NEXT_END,self.after)
        self.assertNotIn(PREVIOUS_END,self.after)
        with self.assertRaises(ValueError):
            derive("wrong source")

    def test_no_host_reply_or_modified_guest_hardware(self):
        for token in ("ipc70_bus.tick(","scheduler.service_one(",
                      "ipc70_bus.write32(","ipc70_ram.write8(",
                      "ctx.mmu.write32("):
            self.assertEqual(self.before.count(token),self.after.count(token))
        for snippet in (CONTINUE,OBSERVER,NEXT_END):
            for token in ("ipc70_bus.write","ipc70_ram.write",
                          "service_one(","ipc70_bus.tick(","ctx.mmu.write"):
                self.assertNotIn(token,snippet)
        self.assertNotRegex(OBSERVER,
            r"\bctx\.(?:msr|pc|lr|srr0|srr1|gpr)\s*=(?!=)")

    def test_sixteen_original_trials_and_private_cleanup(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        self.assertIn("derive_v206_sc_y2_post_flag_harness.py",script)
        self.assertIn("V205_SC_Y2_FLAG verified=1",script)
        self.assertIn("V206_SC_Y2_POST_FLAG verified=1",script)
        self.assertIn(')" -eq 16',script)
        good=("V206_Y2_POST_FLAG call=1 clear=1 down=1 queue=1 guest=1 "
              "caller=1 stepped=1 coherent=1 mapped=1 sc=1 ee=0 pc=80529434 lr=80519388")
        self.assertIsNotNone(re.fullmatch(PASS,good))
        self.assertIsNone(re.fullmatch(PASS,good.replace("queue=1","queue=0")))
        self.assertIsNotNone(re.fullmatch(PATTERN,good.replace("sc=1","sc=0")))
        wf=(HERE.parents[1]/".github/workflows/wii-v206-sc-y2-post-flag.yml").read_text()
        for item in ("run_v206_sc_y2_post_flag.sh",
                     "test_v206_sc_y2_post_flag.py",
                     "V206_SC_Y2_POST_FLAG verified=1"):
            self.assertIn(item,wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)
        with tempfile.TemporaryDirectory() as directory:
            for name,content in (
                ("runner.sh",script),
                ("entry.sh",(HERE/"run_v206_sc_y2_post_flag.sh").read_text())):
                path=Path(directory)/name
                path.write_text(content,encoding="utf-8")
                subprocess.run(["bash","-n",str(path)],check=True)

if __name__=="__main__":
    unittest.main()
