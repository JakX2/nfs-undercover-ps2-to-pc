#!/usr/bin/env python3
"""V223 original-free third Y1 IpcReplyHandler first read native tests."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v222_sc_y1_ipc_next_harness import derive as previous, OBSERVER as PREVIOUS_OBSERVER, NEXT_END as PREVIOUS_END
from derive_v223_sc_y1_reply_read_harness import derive, STOP, CONTINUE, OBSERVER, NEXT_END
from derive_v223_sc_y1_reply_read_runner import derive as runner, PATTERN, PASS
HERE=Path(__file__).resolve().parent
class V223(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=previous(source);cls.after=derive(source)
    def test_original_ipc_read_callsite(self):
        self.assertIn(STOP,PREVIOUS_OBSERVER)
        self.assertNotIn(STOP,self.after)
        self.assertIn(CONTINUE,self.after)
        self.assertIn(OBSERVER,self.after)
        self.assertIn(NEXT_END,self.after)
        self.assertNotIn(PREVIOUS_END,self.after)
        for x in ("v222_next_seen==1u","addr==0x8051905cu",
                  "ctx.lr==0x805190e8u","v222_next_pc==0x805190c0u",
                  "v222_next_lr==0x80519354u",
                  "int32_t(ipc70_ram.read32(v183_second_phys+4u))==IOS::Invalid",
                  "++v223_read_seen"):
            self.assertIn(x,OBSERVER)
        with self.assertRaises(ValueError):derive("wrong")
    def test_no_guest_state_injection(self):
        for token in ("scheduler.service_one(","ipc70_ram.write8(","ipc70_bus.write32(","ctx.mmu.write32("):
            self.assertEqual(self.before.count(token),self.after.count(token))
        for s in (CONTINUE,OBSERVER,NEXT_END):
            for bad in ("ipc70_bus.write","ipc70_ram.write","ctx.mmu.write","ctx.pc=0x"):
                self.assertNotIn(bad,s)
            self.assertNotRegex(s,r"ctx\.gpr\[[0-9]+\]\s*=(?!=)")
    def test_owner_gate_and_cleanup(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for mark in ("derive_v223_sc_y1_reply_read_harness.py","V222_SC_Y1_IPC_NEXT verified=1","V223_SC_Y1_REPLY_READ verified=1"):
            self.assertIn(mark,script)
        line="V223_NEG_REPLY_READ irq=1 wire=1 caller=1 guest=1 masked=1 sc=1 pc=8051905c lr=805190e8"
        self.assertIsNotNone(re.fullmatch(PASS,line))
        self.assertIsNone(re.fullmatch(PASS,line.replace("wire=1","wire=0")))
        self.assertIsNotNone(re.fullmatch(PATTERN,line.replace("guest=1","guest=0")))
        wf=(HERE.parents[1]/".github/workflows/wii-v223-sc-y1-reply-read.yml").read_text()
        for mark in ("run_v223_sc_y1_reply_read.sh","test_v223_sc_y1_reply_read.py","V223_SC_Y1_REPLY_READ verified=1"):
            self.assertIn(mark,wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)
        with tempfile.TemporaryDirectory() as d:
            for name,content in (("runner",script),("wrapper",(HERE/"run_v223_sc_y1_reply_read.sh").read_text())):
                f=Path(d)/name;f.write_text(content,encoding="utf-8")
                subprocess.run(["bash","-n",str(f)],check=True)
if __name__=="__main__":
    unittest.main()
