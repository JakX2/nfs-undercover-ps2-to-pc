#!/usr/bin/env python3
"""V231 original-free AOT-rooted indirect ISFS callback entry tests."""
import re
import sys
sys.setrecursionlimit(6000)
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v230_sc_y1_context_next_harness import derive as previous, OBSERVER as PREVIOUS_OBSERVER, NEXT_END as PREVIOUS_END
from derive_v231_sc_y1_isfs_callback_harness import derive, STOP, CONTINUE, OBSERVER, NEXT_END
from derive_v231_sc_y1_isfs_callback_runner import derive as runner, PATTERN, PASS
HERE=Path(__file__).resolve().parent

class V231(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        src=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=previous(src)
        cls.after=derive(src)

    def test_original_indirect_call_and_negative_reply(self):
        self.assertIn(STOP,PREVIOUS_OBSERVER)
        self.assertNotIn(STOP,self.after)
        self.assertIn(CONTINUE,self.after)
        self.assertIn(OBSERVER,self.after)
        self.assertIn(NEXT_END,self.after)
        self.assertNotIn(PREVIOUS_END,self.after)
        for marker in ("addr==0x804f0e04u","ctx.lr==0x805192acu",
                       "ctx.mmu.read32(request+32u)==addr",
                       "ctx.gpr[3]==uint32_t(IOS::Invalid)",
                       "ctx.gpr[4]==ctx.mmu.read32(request+36u)",
                       "int32_t(ipc70_ram.read32(v183_second_phys+4u))==IOS::Invalid",
                       "v231_context_inst","++v231_callback_seen"):
            self.assertIn(marker,OBSERVER)
        self.assertIn("v231_callback_seen==1u",NEXT_END)
        with self.assertRaises(ValueError):derive("unmatched public fixture")

    def test_no_guest_repair_or_hle_callback(self):
        for marker in ("scheduler.service_one(","ipc70_bus.write32(",
                       "ipc70_ram.write8(","ctx.mmu.write32("):
            self.assertEqual(self.before.count(marker),self.after.count(marker))
        for x in (CONTINUE,OBSERVER,NEXT_END):
            for bad in ("ipc70_bus.write","ipc70_ram.write",
                        "ctx.mmu.write","ctx.pc=0x",
                        "ctx.ctr=","ctx.lr=0x"):
                self.assertNotIn(bad,x)
            self.assertNotRegex(x,r"ctx\.gpr\[[0-9]+\]\s*=(?!=)")

    def test_owner_trials_and_cleanup(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for marker in ("derive_v231_sc_y1_isfs_callback_harness.py",
                       "derive_v225_isfs_callback_generator.py",
                       "V230_SC_Y1_CONTEXT_NEXT verified=1",
                       "V231_SC_Y1_ISFS_CALLBACK verified=1"):
            self.assertIn(marker,script)
        positive="V231_ISFS_CALLBACK clear=1 wire=1 header=1 selected=1 same=1 abi=1 userdata=1 guest=1 sc=1 pc=804f0e04 lr=805192ac"
        self.assertIsNotNone(re.fullmatch(PASS,positive))
        self.assertIsNone(re.fullmatch(PASS,positive.replace("selected=1","selected=0")))
        self.assertIsNotNone(re.fullmatch(PATTERN,positive.replace("abi=1","abi=0")))
        wf=(HERE.parents[1]/".github/workflows/wii-v231-sc-y1-isfs-callback.yml").read_text()
        for m in ("run_v231_sc_y1_isfs_callback.sh",
                  "test_v231_sc_y1_isfs_callback.py",
                  "V231_SC_Y1_ISFS_CALLBACK verified=1"):
            self.assertIn(m,wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)
        with tempfile.TemporaryDirectory() as d:
            for name,content in (("runner",script),
               ("wrapper",(HERE/"run_v231_sc_y1_isfs_callback.sh").read_text())):
                f=Path(d)/name;f.write_text(content,encoding="utf-8")
                subprocess.run(["bash","-n",str(f)],check=True)

if __name__=="__main__":unittest.main()
