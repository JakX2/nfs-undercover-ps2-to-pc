#!/usr/bin/env python3
"""Original-free V213 checks for real post-RFI game-thread execution."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v212_sc_y2_rfi_harness import derive as previous, OBSERVER as PREVIOUS_OBSERVER, NEXT_END as PREVIOUS_END
from derive_v213_sc_y2_thread_next_harness import derive, STOP, CONTINUE, OBSERVER, NEXT_END
from derive_v213_sc_y2_thread_next_runner import derive as runner, PATTERN, PASS
from derive_v185_sc_reply_next_harness import OBSERVER_HEADER
HERE=Path(__file__).resolve().parent

class V213(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=previous(base);cls.after=derive(base)

    def test_rfi_restored_thread_calls_authentic_guest_function(self):
        self.assertIn(STOP,PREVIOUS_OBSERVER)
        self.assertNotIn(STOP,self.after)
        self.assertIn(CONTINUE,self.after)
        self.assertIn(OBSERVER_HEADER+"\n"+OBSERVER,self.after)
        self.assertIn(NEXT_END,self.after)
        self.assertNotIn(PREVIOUS_END,self.after)
        for x in ("v196_live&&v212_rfi_seen==1u&&v213_call_seen==0u",
                  "ctx.inst_count>v213_start_inst",
                  "v213_next_pc=addr;v213_next_lr=ctx.lr",
                  "queued_replies()==1u",
                  "v213_call_seen==1u"):
            self.assertIn(x,OBSERVER+NEXT_END)
        with self.assertRaises(ValueError):derive("unexpected source")

    def test_read_only_guest_and_ios(self):
        for token in ("ipc70_bus.tick(","scheduler.service_one(",
                      "ipc70_bus.write32(","ipc70_ram.write8(",
                      "ctx.mmu.write32("):
            self.assertEqual(self.before.count(token),self.after.count(token))
        for chunk in (CONTINUE,OBSERVER,NEXT_END):
            for illegal in ("ipc70_bus.write","ipc70_ram.write",
                            "service_one(","ipc70_bus.tick(","ctx.mmu.write"):
                self.assertNotIn(illegal,chunk)

    def test_owner_16_trials_and_bounded_output(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for marker in ("derive_v213_sc_y2_thread_next_harness.py",
                       "V212_SC_Y2_RFI verified=1",
                       "V213_SC_Y2_THREAD_NEXT verified=1"):
            self.assertIn(marker,script)
        good="V213_Y2_THREAD guest=1 caller=1 coherent=1 mapped=1 irq_down=1 queued=1 open=1 sc=1 ee=1 pc=8052f830 lr=80520970"
        self.assertIsNotNone(re.fullmatch(PASS,good))
        self.assertIsNotNone(re.fullmatch(PATTERN,good.replace("guest=1","guest=0")))
        self.assertIsNone(re.fullmatch(PASS,good.replace("queued=1","queued=0")))
        wf=(HERE.parents[1]/".github/workflows/wii-v213-sc-y2-thread-next.yml").read_text()
        for marker in ("run_v213_sc_y2_thread_next.sh","test_v213_sc_y2_thread_next.py",
                       "V213_SC_Y2_THREAD_NEXT verified=1"):
            self.assertIn(marker,wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)
        with tempfile.TemporaryDirectory() as td:
            for name,body in (("runner",script),("wrapper",(HERE/"run_v213_sc_y2_thread_next.sh").read_text())):
                p=Path(td)/name;p.write_text(body,encoding="utf-8")
                subprocess.run(["bash","-n",str(p)],check=True)

if __name__=="__main__":
    unittest.main()
