#!/usr/bin/env python3
"""Original-free native third Y1 vector-to-handler regression for V216."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v215_sc_y1_negative_vector_harness import derive as previous, CONTINUE as PREVIOUS_CONTINUE, NEXT_END as PREVIOUS_END
from derive_v216_sc_y1_handler_harness import derive, STOP, CONTINUE, OBSERVER, NEXT_END
from derive_v216_sc_y1_handler_runner import derive as runner, ENTRY, PATTERN, PASS
HERE=Path(__file__).resolve().parent

class V216(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        src=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=previous(src);cls.after=derive(src)

    def test_original_vector_executes_to_native_handler(self):
        self.assertIn(STOP,PREVIOUS_CONTINUE)
        self.assertNotIn(STOP,self.after)
        self.assertIn(CONTINUE,self.after)
        self.assertIn(OBSERVER,self.after)
        self.assertIn(NEXT_END,self.after)
        self.assertNotIn(PREVIOUS_END,self.after)
        for marker in ("addr==undercover::wii::ExternalVector",
                       "addr==0x80526ce0u",
                       "ctx.inst_count>v216_start_inst",
                       "irq74_vector[i]",
                       "int32_t(ipc70_ram.read32(v183_second_phys+4u))==VI::Invalid",
                       "ctx.gpr[3]==4u","++v216_handler_seen"):
            self.assertIn(marker,OBSERVER)
        with self.assertRaises(ValueError):derive("unmatched")

    def test_no_guest_register_or_response_forgery(self):
        for needle in ("ipc70_bus.tick(","scheduler.service_one(",
                       "ctx.mmu.write32(","ipc70_ram.write8(",
                       "ipc70_bus.write32("):
            self.assertEqual(self.before.count(needle),self.after.count(needle))
        for snippet in (CONTINUE,OBSERVER,NEXT_END):
            for bad in ("ipc70_bus.write","ipc70_ram.write","ctx.mmu.write",
                        "ctx.pc=0x80000500"):
                self.assertNotIn(bad,snippet)
            self.assertNotRegex(snippet,r"ctx\.gpr\[3\]\s*=(?!=)")

    def test_sixteen_trial_owner_and_cleanup(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for x in ("derive_v216_sc_y1_handler_harness.py",
                  "V215_SC_Y1_NEGATIVE_VECTOR verified=1",
                  "V216_SC_Y1_HANDLER verified=1"):
            self.assertIn(x,script)
        good="V216_Y1_HANDLER vector=1 irq=1 reply=1 index=1 context=1 masked=1 progressed=1 pc=80526ce0 lr=80526ce0"
        self.assertIsNotNone(re.fullmatch(PASS,good))
        self.assertIsNotNone(re.fullmatch(PATTERN,good.replace("reply=1","reply=0")))
        self.assertIsNone(re.fullmatch(PASS,good.replace("irq=1","irq=0")))
        self.assertIsNotNone(re.fullmatch(ENTRY,"V216_Y1_ENTRY saved=1 regs=1 bytes=1 masked=1 y1=1 negative=1"))
        wf=(HERE.parents[1]/".github/workflows/wii-v216-sc-y1-handler.yml").read_text()
        for x in ("run_v216_sc_y1_handler.sh","test_v216_sc_y1_handler.py",
                  "V216_SC_Y1_HANDLER verified=1"):
            self.assertIn(x,wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)
        with tempfile.TemporaryDirectory() as tmp:
            for n,content in (("runner",script),("wrapper",(HERE/"run_v216_sc_y1_handler.sh").read_text())):
                path=Path(tmp)/n;path.write_text(content,encoding="utf-8")
                subprocess.run(["bash","-n",str(path)],check=True)

if __name__=="__main__":
    unittest.main()
