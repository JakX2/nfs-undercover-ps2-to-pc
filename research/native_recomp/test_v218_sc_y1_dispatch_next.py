#!/usr/bin/env python3
"""V218 original-free native negative IOS Y1 dispatcher regression."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v217_sc_y1_dispatch_harness import derive as previous, OBSERVER as PREVIOUS_OBSERVER, NEXT_END as PREVIOUS_END
from derive_v218_sc_y1_dispatch_next_harness import derive, STOP, CONTINUE, OBSERVER, NEXT_END
from derive_v218_sc_y1_dispatch_next_runner import derive as runner, PATTERN, PASS
HERE=Path(__file__).resolve().parent
class V218(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=previous(base);cls.after=derive(base)
    def test_native_original_second_y1_dispatch_successor(self):
        self.assertIn(STOP,PREVIOUS_OBSERVER)
        self.assertNotIn(STOP,self.after)
        self.assertIn(CONTINUE,self.after)
        self.assertIn(OBSERVER,self.after)
        self.assertIn(NEXT_END,self.after)
        self.assertNotIn(PREVIOUS_END,self.after)
        for token in ("v217_dispatch_seen==1u",
                      "addr>=0x80400000u&&addr<0x80600000u",
                      "ctx.lr>=0x80526a3cu&&ctx.lr<0x80526ce0u",
                      "int32_t(ipc70_ram.read32(v183_second_phys+4u))==IOS::Invalid",
                      "ctx.inst_count>v218_dispatch_inst","++v218_next_seen"):
            self.assertIn(token,OBSERVER)
        with self.assertRaises(ValueError):derive("invalid base")
    def test_only_observe_original_game_and_ios_state(self):
        for needle in ("scheduler.service_one(","ipc70_ram.write8(",
                       "ipc70_bus.write32(","ctx.mmu.write32("):
            self.assertEqual(self.before.count(needle),self.after.count(needle))
        for content in (CONTINUE,OBSERVER,NEXT_END):
            for bad in ("ipc70_bus.write","ipc70_ram.write","ctx.mmu.write","ctx.pc=0x"):
                self.assertNotIn(bad,content)
            self.assertNotRegex(content,r"ctx\.gpr\[[0-9]+\]\s*=(?!=)")
    def test_owner_16_trial_script_and_cleanup(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        self.assertIn("V218_SC_Y1_DISPATCH_NEXT verified=1",script)
        self.assertIn("V217_SC_Y1_NEG_DISPATCH verified=1",script)
        line="V218_NEG_NEXT irq=1 reply=1 guest=1 caller=1 masked=1 sc=1 pc=8051b060 lr=80526b40"
        self.assertIsNotNone(re.fullmatch(PASS,line))
        self.assertIsNone(re.fullmatch(PASS,line.replace("irq=1","irq=0")))
        self.assertIsNotNone(re.fullmatch(PATTERN,line.replace("masked=1","masked=0")))
        wf=(HERE.parents[1]/".github/workflows/wii-v218-sc-y1-dispatch-next.yml").read_text()
        for name in ("run_v218_sc_y1_dispatch_next.sh","test_v218_sc_y1_dispatch_next.py",
                     "V218_SC_Y1_DISPATCH_NEXT verified=1"):
            self.assertIn(name,wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)
        with tempfile.TemporaryDirectory() as temp:
            for name,content in (("runner.sh",script),
                                 ("entry.sh",(HERE/"run_v218_sc_y1_dispatch_next.sh").read_text())):
                p=Path(temp)/name;p.write_text(content,encoding="utf-8")
                subprocess.run(["bash","-n",str(p)],check=True)
if __name__=="__main__":
    unittest.main()
