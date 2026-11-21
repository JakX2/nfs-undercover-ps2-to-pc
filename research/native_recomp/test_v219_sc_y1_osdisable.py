#!/usr/bin/env python3
"""Original-free V219 third negative Y1 OSGetTime and scheduler regression."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v218_sc_y1_dispatch_next_harness import derive as previous, OBSERVER as PREVIOUS_OBSERVER, NEXT_END as PREVIOUS_END
from derive_v219_sc_y1_osdisable_harness import derive, STOP, CONTINUE, OBSERVER, NEXT_END
from derive_v219_sc_y1_osdisable_runner import derive as runner, PATTERN, PASS
HERE=Path(__file__).resolve().parent
class V219(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=previous(base);cls.after=derive(base)
    def test_original_guest_returns_from_osgettime(self):
        self.assertIn(STOP,PREVIOUS_OBSERVER)
        self.assertNotIn(STOP,self.after)
        self.assertIn(CONTINUE,self.after)
        self.assertIn(OBSERVER,self.after)
        self.assertIn(NEXT_END,self.after)
        self.assertNotIn(PREVIOUS_END,self.after)
        for token in ("v218_next_seen==1u","addr==0x805293f8u",
                      "ctx.lr==0x80526c98u","ctx.inst_count>v219_osgettime_inst",
                      "int32_t(ipc70_ram.read32(v183_second_phys+4u))==IOS::Invalid",
                      "++v219_disable_seen"):
            self.assertIn(token,OBSERVER)
        with self.assertRaises(ValueError):derive("wrong base")
    def test_does_not_write_guest_or_modify_ios(self):
        for token in ("scheduler.service_one(","ipc70_ram.write8(",
                      "ipc70_bus.write32(","ctx.mmu.write32("):
            self.assertEqual(self.before.count(token),self.after.count(token))
        for block in (CONTINUE,OBSERVER,NEXT_END):
            for bad in ("ipc70_bus.write","ipc70_ram.write","ctx.mmu.write","ctx.pc=0x"):
                self.assertNotIn(bad,block)
            self.assertNotRegex(block,r"ctx\.gpr\[[0-9]+\]\s*=(?!=)")
    def test_sixteen_original_runs_and_cleanup(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        self.assertIn("V218_SC_Y1_DISPATCH_NEXT verified=1",script)
        self.assertIn("V219_SC_Y1_OSDISABLE verified=1",script)
        match="V219_NEG_OSDI guest=1 caller=1 masked=1 irq=1 reply=1 sc=1 pc=805293f8 lr=80526c98"
        self.assertIsNotNone(re.fullmatch(PASS,match))
        self.assertIsNone(re.fullmatch(PASS,match.replace("reply=1","reply=0")))
        self.assertIsNotNone(re.fullmatch(PATTERN,match.replace("guest=1","guest=0")))
        wf=(HERE.parents[1]/".github/workflows/wii-v219-sc-y1-osdisable.yml").read_text()
        for token in ("run_v219_sc_y1_osdisable.sh","test_v219_sc_y1_osdisable.py",
                      "V219_SC_Y1_OSDISABLE verified=1"):
            self.assertIn(token,wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)
        with tempfile.TemporaryDirectory() as directory:
            for name,data in (("runner.sh",script),
                              ("entry.sh",(HERE/"run_v219_sc_y1_osdisable.sh").read_text())):
                p=Path(directory)/name;p.write_text(data,encoding="utf-8")
                subprocess.run(["bash","-n",str(p)],check=True)
if __name__=="__main__":
    unittest.main()
