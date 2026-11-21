#!/usr/bin/env python3
"""V226 original-free successor and 16-trial owner-native guards."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v224_sc_y1_reply_second_read_harness import derive as previous, OBSERVER as PREVIOUS_OBSERVER, NEXT_END as PREVIOUS_END
from derive_v226_sc_y1_reply_successor_harness import derive, STOP, CONTINUE, OBSERVER, NEXT_END
from derive_v226_sc_y1_reply_successor_runner import derive as runner, PATTERN, PASS
HERE=Path(__file__).resolve().parent

class V226(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        src=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=previous(src)
        cls.after=derive(src)

    def test_original_ppc_successor(self):
        self.assertIn(STOP,PREVIOUS_OBSERVER)
        self.assertNotIn(STOP,self.after)
        self.assertIn(CONTINUE,self.after)
        self.assertIn(OBSERVER,self.after)
        self.assertIn(NEXT_END,self.after)
        self.assertNotIn(PREVIOUS_END,self.after)
        for mark in ("v224_second_seen==1u","v226_successor_seen==0u",
                     "ctx.inst_count>v226_start_inst",
                     "int32_t(ipc70_ram.read32(v183_second_phys+4u))==IOS::Invalid",
                     "ctx.gpr[13]==v147_first_r13",
                     "++v226_successor_seen"):
            self.assertIn(mark,OBSERVER)
        with self.assertRaises(ValueError):derive("missing source")

    def test_no_guest_state_or_ios_reply_forgery(self):
        for mark in ("scheduler.service_one(","ipc70_bus.write32(",
                     "ipc70_ram.write8(","ctx.mmu.write32("):
            self.assertEqual(self.before.count(mark),self.after.count(mark))
        for src in (CONTINUE,OBSERVER,NEXT_END):
            for bad in ("ipc70_bus.write","ipc70_ram.write",
                        "ctx.mmu.write","ctx.pc=0x"):
                self.assertNotIn(bad,src)
            self.assertNotRegex(src,r"ctx\.gpr\[[0-9]+\]\s*=(?!=)")

    def test_runner_and_owner_cleanup(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for s in ("derive_v226_sc_y1_reply_successor_harness.py",
                  "V224_SC_Y1_SECOND_READ verified=1",
                  "V226_SC_Y1_REPLY_SUCCESSOR verified=1"):
            self.assertIn(s,script)
        good="V226_NEG_SUCCESSOR signal=1 negative=1 guest=1 caller=1 sc=1 pc=8051906c lr=8051910c"
        self.assertIsNotNone(re.fullmatch(PASS,good))
        self.assertIsNone(re.fullmatch(PASS,good.replace("guest=1","guest=0")))
        self.assertIsNotNone(re.fullmatch(PATTERN,good.replace("signal=1","signal=0")))
        wf=(HERE.parents[1]/".github/workflows/wii-v226-sc-y1-reply-successor.yml").read_text()
        for mark in ("run_v226_sc_y1_reply_successor.sh",
                     "test_v226_sc_y1_reply_successor.py",
                     "V226_SC_Y1_REPLY_SUCCESSOR verified=1"):
            self.assertIn(mark,wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)
        with tempfile.TemporaryDirectory() as d:
            for name,content in (("runner",script),
                                 ("wrapper",(HERE/"run_v226_sc_y1_reply_successor.sh").read_text())):
                file=Path(d)/name;file.write_text(content,encoding="utf-8")
                subprocess.run(["bash","-n",str(file)],check=True)

if __name__=="__main__":
    unittest.main()
