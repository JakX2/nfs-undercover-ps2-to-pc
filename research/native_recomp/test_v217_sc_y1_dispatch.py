#!/usr/bin/env python3
"""V217 source-only negative third Y1 PowerPC handler dispatcher tests."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v216_sc_y1_handler_harness import derive as previous, OBSERVER as PREVIOUS_OBSERVER, NEXT_END as PREVIOUS_END
from derive_v217_sc_y1_dispatch_harness import derive, STOP, CONTINUE, OBSERVER, NEXT_END
from derive_v217_sc_y1_dispatch_runner import derive as runner, PATTERN, PASS
HERE=Path(__file__).resolve().parent

class V217(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=previous(source);cls.after=derive(source)

    def test_original_negative_y1_handler_enters_dispatch(self):
        self.assertIn(STOP,PREVIOUS_OBSERVER)
        self.assertNotIn(STOP,self.after)
        self.assertIn(CONTINUE,self.after)
        self.assertIn(OBSERVER,self.after)
        self.assertIn(NEXT_END,self.after)
        self.assertNotIn(PREVIOUS_END,self.after)
        for marker in ("v216_handler_seen==1u&&v217_dispatch_seen==0u",
                       "addr==0x80526a3cu&&ctx.pc==addr",
                       "ctx.gpr[3]==4u","ctx.gpr[4]==THREAD",
                       "ctx.inst_count>v217_handler_inst",
                       "int32_t(ipc70_ram.read32(v183_second_phys+4u))==VI::Invalid",
                       "++v217_dispatch_seen"):
            self.assertIn(marker,OBSERVER)
        with self.assertRaises(ValueError):derive("wrong source")

    def test_guest_state_and_native_ios_unchanged(self):
        for needle in ("ipc70_bus.tick(","scheduler.service_one(",
                       "ctx.mmu.write32(","ipc70_ram.write8(",
                       "ipc70_bus.write32("):
            self.assertEqual(self.before.count(needle),self.after.count(needle))
        for part in (CONTINUE,OBSERVER,NEXT_END):
            for bad in ("ipc70_bus.write","ipc70_ram.write",
                        "ctx.mmu.write","ctx.pc=0x80526a3c"):
                self.assertNotIn(bad,part)
            self.assertNotRegex(part,r"ctx\.gpr\[[34]\]\s*=(?!=)")

    def test_16_trials_and_owner_cleanup(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for marker in ("derive_v217_sc_y1_dispatch_harness.py",
                       "V216_SC_Y1_HANDLER verified=1",
                       "V217_SC_Y1_NEG_DISPATCH verified=1"):
            self.assertIn(marker,script)
        good="V217_NEG_DISPATCH index=1 context=1 masked=1 irq=1 reply=1 guest=1 saved=1 pc=80526a3c lr=80526ce0"
        self.assertIsNotNone(re.fullmatch(PASS,good))
        self.assertIsNotNone(re.fullmatch(PATTERN,good.replace("guest=1","guest=0")))
        self.assertIsNone(re.fullmatch(PASS,good.replace("irq=1","irq=0")))
        wf=(HERE.parents[1]/".github/workflows/wii-v217-sc-y1-dispatch.yml").read_text()
        for m in ("run_v217_sc_y1_dispatch.sh",
                  "test_v217_sc_y1_dispatch.py",
                  "V217_SC_Y1_NEG_DISPATCH verified=1"):
            self.assertIn(m,wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)
        with tempfile.TemporaryDirectory() as folder:
            for name,content in (("runner",script),("wrapper",(HERE/"run_v217_sc_y1_dispatch.sh").read_text())):
                path=Path(folder)/name;path.write_text(content,encoding="utf-8")
                subprocess.run(["bash","-n",str(path)],check=True)

if __name__=="__main__":
    unittest.main()
