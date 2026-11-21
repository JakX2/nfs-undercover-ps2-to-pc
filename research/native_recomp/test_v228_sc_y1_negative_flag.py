#!/usr/bin/env python3
"""V228 original-free Hollywood W1C and negative Y1 reply guards."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v227_sc_y1_negative_ack_harness import derive as previous, ACK as PREVIOUS_ACK, NEXT_END as PREVIOUS_END
from derive_v228_sc_y1_negative_flag_harness import derive, STOP, CONTINUE, OBSERVER, NEXT_END
from derive_v228_sc_y1_negative_flag_runner import derive as runner, PATTERN, PASS
HERE=Path(__file__).resolve().parent

class V228(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        src=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=previous(src)
        cls.after=derive(src)

    def test_real_guest_flag_ack(self):
        self.assertIn(STOP,PREVIOUS_ACK)
        self.assertNotIn(STOP,self.after)
        self.assertIn(CONTINUE,self.after)
        self.assertIn(OBSERVER,self.after)
        self.assertIn(NEXT_END,self.after)
        self.assertNotIn(PREVIOUS_END,self.after)
        for token in ("addr==0x80522294u","ctx.lr==0x80519124u",
                      "write.second&H::IPC_PPC","flag_writes==1u",
                      "(*flag&H::IPC_PPC)==0u",
                      "int32_t(ipc70_ram.read32(v183_second_phys+4u))==IOS::Invalid",
                      "++v228_next_seen"):
            self.assertIn(token,OBSERVER)
        with self.assertRaises(ValueError):derive("missing")

    def test_no_host_synthesized_irq_clear(self):
        for t in ("scheduler.service_one(","ipc70_bus.write32(",
                  "ipc70_ram.write8(","ctx.mmu.write32("):
            self.assertEqual(self.before.count(t),self.after.count(t))
        for x in (CONTINUE,OBSERVER,NEXT_END):
            for forbidden in ("ipc70_bus.write","ipc70_ram.write",
                              "ctx.mmu.write","ctx.pc=0x"):
                self.assertNotIn(forbidden,x)
            self.assertNotRegex(x,r"ctx\.gpr\[[0-9]+\]\s*=(?!=)")

    def test_sixteen_owner_trials_and_private_cleanup(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for m in ("derive_v228_sc_y1_negative_flag_harness.py",
                  "V227_SC_Y1_NEGATIVE_ACK verified=1",
                  "V228_SC_Y1_NEGATIVE_FLAG verified=1"):
            self.assertIn(m,script)
        good="V228_NEG_FLAG y1=1 w1c=1 flag=1 irq_down=1 reply=1 guest=1 sc=1 pc=80522294 lr=80519124"
        self.assertIsNotNone(re.fullmatch(PASS,good))
        self.assertIsNone(re.fullmatch(PASS,good.replace("w1c=1","w1c=0")))
        self.assertIsNotNone(re.fullmatch(PATTERN,good.replace("guest=1","guest=0")))
        wf=(HERE.parents[1]/".github/workflows/wii-v228-sc-y1-negative-flag.yml").read_text()
        for mark in ("run_v228_sc_y1_negative_flag.sh",
                     "test_v228_sc_y1_negative_flag.py",
                     "V228_SC_Y1_NEGATIVE_FLAG verified=1"):
            self.assertIn(mark,wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)
        with tempfile.TemporaryDirectory() as d:
            for name,content in (("runner",script),
                 ("wrapper",(HERE/"run_v228_sc_y1_negative_flag.sh").read_text())):
                f=Path(d)/name;f.write_text(content,encoding="utf-8")
                subprocess.run(["bash","-n",str(f)],check=True)

if __name__=="__main__":
    unittest.main()
