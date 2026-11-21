#!/usr/bin/env python3
"""V224 original-free negative Y1 second IPC register read tests."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v223_sc_y1_reply_read_harness import derive as previous, OBSERVER as PREVIOUS_OBSERVER, NEXT_END as PREVIOUS_END
from derive_v224_sc_y1_reply_second_read_harness import derive, STOP, CONTINUE, OBSERVER, NEXT_END
from derive_v224_sc_y1_reply_second_read_runner import derive as runner, PATTERN, PASS
HERE=Path(__file__).resolve().parent
class V224(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        src=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=previous(src);cls.after=derive(src)
    def test_second_original_ipc_read_entry(self):
        self.assertIn(STOP,PREVIOUS_OBSERVER)
        self.assertNotIn(STOP,self.after)
        self.assertIn(CONTINUE,self.after)
        self.assertIn(OBSERVER,self.after)
        self.assertIn(NEXT_END,self.after)
        self.assertNotIn(PREVIOUS_END,self.after)
        for mark in ("v223_read_seen==1u","addr==0x8051905cu",
                     "ctx.lr==0x805190fcu","ctx.inst_count>v224_first_inst",
                     "int32_t(ipc70_ram.read32(v183_second_phys+4u))==IOS::Invalid",
                     "++v224_second_seen"):
            self.assertIn(mark,OBSERVER)
        with self.assertRaises(ValueError):derive("missing source")
    def test_observers_only(self):
        for token in ("scheduler.service_one(","ipc70_ram.write8(",
                      "ipc70_bus.write32(","ctx.mmu.write32("):
            self.assertEqual(self.before.count(token),self.after.count(token))
        for src in (CONTINUE,OBSERVER,NEXT_END):
            for prohibited in ("ipc70_bus.write","ipc70_ram.write",
                               "ctx.mmu.write","ctx.pc=0x"):
                self.assertNotIn(prohibited,src)
            self.assertNotRegex(src,r"ctx\.gpr\[[0-9]+\]\s*=(?!=)")
    def test_sixteen_trials_and_owner_separation(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for mark in ("derive_v224_sc_y1_reply_second_read_harness.py",
                     "V223_SC_Y1_REPLY_READ verified=1",
                     "V224_SC_Y1_SECOND_READ verified=1"):
            self.assertIn(mark,script)
        correct="V224_NEG_SECOND_READ irq=1 wire=1 guest=1 masked=1 sc=1 pc=8051905c lr=805190fc"
        self.assertIsNotNone(re.fullmatch(PASS,correct))
        self.assertIsNone(re.fullmatch(PASS,correct.replace("irq=1","irq=0")))
        self.assertIsNotNone(re.fullmatch(PATTERN,correct.replace("wire=1","wire=0")))
        wf=(HERE.parents[1]/".github/workflows/wii-v224-sc-y1-reply-second-read.yml").read_text()
        for mark in ("run_v224_sc_y1_reply_second_read.sh",
                     "test_v224_sc_y1_reply_second_read.py",
                     "V224_SC_Y1_SECOND_READ verified=1"):
            self.assertIn(mark,wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)
        with tempfile.TemporaryDirectory() as d:
            for name,script_text in (("runner",script),("wrapper",(HERE/"run_v224_sc_y1_reply_second_read.sh").read_text())):
                f=Path(d)/name;f.write_text(script_text,encoding="utf-8")
                subprocess.run(["bash","-n",str(f)],check=True)
if __name__=="__main__":
    unittest.main()
