#!/usr/bin/env python3
"""V229 source-only post-cache guest continuation and indirect AOT root."""
import re
import sys
sys.setrecursionlimit(6000)
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v228_sc_y1_negative_flag_harness import derive as previous, OBSERVER as PREVIOUS_OBSERVER, NEXT_END as PREVIOUS_END
from derive_v229_sc_y1_post_cache_harness import derive, STOP, CONTINUE, OBSERVER, NEXT_END
from derive_v229_sc_y1_post_cache_runner import derive as runner, PATTERN, PASS
HERE=Path(__file__).resolve().parent
class V229(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        src=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=previous(src);cls.after=derive(src)
    def test_genuine_post_cache_guest_call(self):
        self.assertIn(STOP,PREVIOUS_OBSERVER)
        self.assertNotIn(STOP,self.after)
        self.assertIn(CONTINUE,self.after)
        self.assertIn(OBSERVER,self.after)
        self.assertIn(NEXT_END,self.after)
        self.assertNotIn(PREVIOUS_END,self.after)
        for needle in ("v228_next_seen==1u","ctx.inst_count>v229_start_inst",
                       "addr>=0x80400000u","ctx.gpr[13]==v147_first_r13",
                       "int32_t(ipc70_ram.read32(v183_second_phys+4u))==IOS::Invalid",
                       "++v229_call_seen"):
            self.assertIn(needle,OBSERVER)
        with self.assertRaises(ValueError):derive("invalid fixture")
    def test_no_guest_or_reply_forgery(self):
        for mark in ("ipc70_bus.write32(","ipc70_ram.write8(",
                     "ctx.mmu.write32(","scheduler.service_one("):
            self.assertEqual(self.before.count(mark),self.after.count(mark))
        for code in (CONTINUE,OBSERVER,NEXT_END):
            for bad in ("ipc70_bus.write","ipc70_ram.write",
                        "ctx.mmu.write","ctx.pc=0x"):
                self.assertNotIn(bad,code)
            self.assertNotRegex(code,r"ctx\.gpr\[[0-9]+\]\s*=(?!=)")
    def test_owner_runner_and_aot_root(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for needle in ("derive_v229_sc_y1_post_cache_harness.py",
                       "derive_v225_isfs_callback_generator.py",
                       "V229_CALLBACK_ROOT verified=1",
                       "V228_SC_Y1_NEGATIVE_FLAG verified=1",
                       "V229_SC_Y1_POST_CACHE verified=1"):
            self.assertIn(needle,script)
        good="V229_NEG_POST_CACHE clear=1 negative=1 guest=1 caller=1 sc=1 context=1 callback=0 pc=80522af4 lr=80519290"
        self.assertIsNotNone(re.fullmatch(PASS,good))
        self.assertIsNone(re.fullmatch(PASS,good.replace("clear=1","clear=0")))
        self.assertIsNotNone(re.fullmatch(PATTERN,good.replace("sc=1","sc=0")))
        wf=(HERE.parents[1]/".github/workflows/wii-v229-sc-y1-post-cache.yml").read_text()
        for needle in ("run_v229_sc_y1_post_cache.sh",
                       "test_v229_sc_y1_post_cache.py",
                       "V229_SC_Y1_POST_CACHE verified=1"):
            self.assertIn(needle,wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)
        with tempfile.TemporaryDirectory() as d:
            for name,txt in (("runner",script),
              ("wrapper",(HERE/"run_v229_sc_y1_post_cache.sh").read_text())):
                f=Path(d)/name;f.write_text(txt,encoding="utf-8")
                subprocess.run(["bash","-n",str(f)],check=True)
if __name__=="__main__":unittest.main()
