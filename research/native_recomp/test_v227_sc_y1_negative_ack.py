#!/usr/bin/env python3
"""V227 original-free native PPCCTRL Y1 W1C and owner fixture regression."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v226_sc_y1_reply_successor_harness import derive as previous, OBSERVER as PREVIOUS_OBSERVER, NEXT_END as PREVIOUS_END
from derive_v227_sc_y1_negative_ack_harness import derive, STOP, CONTINUE, ACK, NEXT_END
from derive_v227_sc_y1_negative_ack_runner import derive as runner, PATTERN, PASS
HERE=Path(__file__).resolve().parent

class V227(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        src=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=previous(src);cls.after=derive(src)

    def test_genuine_w1c_and_negative_reply(self):
        self.assertIn(STOP,PREVIOUS_OBSERVER)
        self.assertNotIn(STOP,self.after)
        self.assertIn(CONTINUE,self.after)
        self.assertIn(ACK,self.after)
        self.assertIn(NEXT_END,self.after)
        self.assertNotIn(PREVIOUS_END,self.after)
        for mark in ("(value&M::Y1)!=0u","(*control&M::Y1)==0u",
                     "(*flags&H::IPC_PPC)!=0u",
                     "int32_t(ipc70_ram.read32(v183_second_phys+4u))==IOS::Invalid",
                     "ipc70_ram.cpu->inst_count>v227_writer_inst",
                     "++v227_ack_seen"):
            self.assertIn(mark,ACK)
        self.assertIn("v227_ack_seen==1u",NEXT_END)
        with self.assertRaises(ValueError):derive("invalid source")

    def test_no_host_generated_ack_or_guest_patch(self):
        for mark in ("scheduler.service_one(","ctx.mmu.write32(",
                     "ipc70_bus.write32(","ipc70_ram.write8("):
            self.assertEqual(self.before.count(mark),self.after.count(mark))
        for src in (CONTINUE,ACK,NEXT_END):
            for bad in ("ipc70_bus.write","ipc70_ram.write",
                        "ctx.mmu.write","ctx.pc=0x"):
                self.assertNotIn(bad,src)
            self.assertNotRegex(src,r"ctx\.gpr\[[0-9]+\]\s*=(?!=)")

    def test_sixteen_real_trials_and_clean_private_fixture(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for mark in ("derive_v227_sc_y1_negative_ack_harness.py",
                     "V226_SC_Y1_REPLY_SUCCESSOR verified=1",
                     "V227_SC_Y1_NEGATIVE_ACK verified=1"):
            self.assertIn(mark,script)
        good="V227_NEG_Y1_ACK wrote=1 cleared=1 flag=1 irq=1 wire=1 guest=1 advanced=1 sc=1"
        self.assertIsNotNone(re.fullmatch(PASS,good))
        self.assertIsNone(re.fullmatch(PASS,good.replace("cleared=1","cleared=0")))
        self.assertIsNotNone(re.fullmatch(PATTERN,good.replace("wire=1","wire=0")))
        wf=(HERE.parents[1]/".github/workflows/wii-v227-sc-y1-negative-ack.yml").read_text()
        for mark in ("run_v227_sc_y1_negative_ack.sh",
                     "test_v227_sc_y1_negative_ack.py",
                     "V227_SC_Y1_NEGATIVE_ACK verified=1"):
            self.assertIn(mark,wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)
        with tempfile.TemporaryDirectory() as tmp:
            for name,script_text in (("runner",script),
               ("wrapper",(HERE/"run_v227_sc_y1_negative_ack.sh").read_text())):
                f=Path(tmp)/name;f.write_text(script_text,encoding="utf-8")
                subprocess.run(["bash","-n",str(f)],check=True)

if __name__=="__main__":
    unittest.main()
