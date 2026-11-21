#!/usr/bin/env python3
"""V230 source-only original OS context continuation regression."""
import re
import sys
sys.setrecursionlimit(6000)
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v229_sc_y1_post_cache_harness import derive as previous, OBSERVER as PREVIOUS_OBSERVER, NEXT_END as PREVIOUS_END
from derive_v230_sc_y1_context_next_harness import derive, STOP, CONTINUE, OBSERVER, NEXT_END
from derive_v230_sc_y1_context_next_runner import derive as runner, PATTERN, PASS
HERE=Path(__file__).resolve().parent
class V230(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        src=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=previous(src);cls.after=derive(src)
    def test_original_osclear_to_osset(self):
        self.assertIn(STOP,PREVIOUS_OBSERVER)
        self.assertNotIn(STOP,self.after)
        self.assertIn(CONTINUE,self.after)
        self.assertIn(OBSERVER,self.after)
        self.assertIn(NEXT_END,self.after)
        self.assertNotIn(PREVIOUS_END,self.after)
        for mark in ("addr==0x805228ccu","ctx.lr==0x80519298u",
                     "ctx.inst_count>v230_start_inst",
                     "ctx.gpr[3]==ctx.gpr[1]+8u",
                     "int32_t(ipc70_ram.read32(v183_second_phys+4u))==IOS::Invalid",
                     "++v230_context_seen"):
            self.assertIn(mark,OBSERVER)
        with self.assertRaises(ValueError):derive("invalid original-free fixture")
    def test_no_synthetic_guest_or_hw_state(self):
        for mark in ("scheduler.service_one(","ipc70_bus.write32(",
                     "ipc70_ram.write8(","ctx.mmu.write32("):
            self.assertEqual(self.before.count(mark),self.after.count(mark))
        for src in (CONTINUE,OBSERVER,NEXT_END):
            for bad in ("ipc70_bus.write","ipc70_ram.write",
                        "ctx.mmu.write","ctx.pc=0x"):
                self.assertNotIn(bad,src)
            self.assertNotRegex(src,r"ctx\.gpr\[[0-9]+\]\s*=(?!=)")
    def test_owner_trials_and_cleanup(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for mark in ("derive_v230_sc_y1_context_next_harness.py",
                     "V229_SC_Y1_POST_CACHE verified=1",
                     "V230_SC_Y1_CONTEXT_NEXT verified=1",
                     "derive_v225_isfs_callback_generator.py"):
            self.assertIn(mark,script)
        good="V230_CONTEXT_NEXT irq_down=1 wire=1 guest=1 context=1 sc=1 pc=805228cc lr=80519298"
        self.assertIsNotNone(re.fullmatch(PASS,good))
        self.assertIsNone(re.fullmatch(PASS,good.replace("context=1","context=0")))
        self.assertIsNotNone(re.fullmatch(PATTERN,good.replace("wire=1","wire=0")))
        wf=(HERE.parents[1]/".github/workflows/wii-v230-sc-y1-context-next.yml").read_text()
        for m in ("run_v230_sc_y1_context_next.sh",
                  "test_v230_sc_y1_context_next.py",
                  "V230_SC_Y1_CONTEXT_NEXT verified=1"):
            self.assertIn(m,wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)
        with tempfile.TemporaryDirectory() as d:
            for name,content in (("runner",script),
               ("wrapper",(HERE/"run_v230_sc_y1_context_next.sh").read_text())):
                f=Path(d)/name;f.write_text(content,encoding="utf-8")
                subprocess.run(["bash","-n",str(f)],check=True)
if __name__=="__main__":unittest.main()
