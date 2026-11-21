#!/usr/bin/env python3
"""V232 original-free ISFS nested callback and NAND AOT root tests."""
import re
import sys
sys.setrecursionlimit(6000)
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v231_sc_y1_isfs_callback_harness import derive as previous, OBSERVER as PREVIOUS_OBSERVER, NEXT_END as PREVIOUS_END
from derive_v232_sc_isfs_callback_next_harness import derive, STOP, CONTINUE, OBSERVER, NEXT_END, OPEN71_OLD, OPEN71_SCOPED, OPEN71_OLD, OPEN71_SCOPED
from derive_v232_sc_isfs_callback_next_runner import derive as runner, PATTERN, PASS
from derive_v232_nand_callback_generator import derive as derive_generator, NEW_ROOTS
HERE=Path(__file__).resolve().parent
class V232(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        src=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=previous(src);cls.after=derive(src)
    def test_actual_powerpc_callback_body(self):
        self.assertIn(STOP,PREVIOUS_OBSERVER)
        self.assertNotIn(STOP,self.after)
        self.assertIn(CONTINUE,self.after)
        self.assertIn(OBSERVER,self.after)
        self.assertIn(NEXT_END,self.after)
        self.assertEqual(self.before.count(OPEN71_OLD),1)
        self.assertEqual(self.after.count(OPEN71_SCOPED),1)
        self.assertIn("if(v231_callback_seen==1u)return false;",OPEN71_SCOPED)
        self.assertNotIn(OPEN71_OLD,self.after)
        self.assertNotIn(PREVIOUS_END,self.after)
        for m in ("v231_callback_seen==1u","ctx.inst_count>v232_start_inst",
                  "ctx.lr>=0x80400000u","ctx.lr<0x80600000u",
                  "data+256u","data+260u",
                  "ctx.gpr[3]==uint32_t(IOS::Invalid)",
                  "V232_ISFS_NEXT","++v232_next_seen"):
            self.assertIn(m,OBSERVER)
        with self.assertRaises(ValueError):derive("missing original-free fixture")
    def test_original_first_open_allocator_observer_is_phase_specific(self):
        self.assertIn(OPEN71_OLD,self.before)
        self.assertNotIn(OPEN71_OLD,self.after)
        self.assertIn(OPEN71_SCOPED,self.after)
        self.assertEqual(self.after.count(OPEN71_SCOPED),1)
        self.assertIn("v231_callback_seen==1u",OPEN71_SCOPED)
        self.assertIn("native IOS_Open allocator tail entry differs",OPEN71_SCOPED)
        self.assertIn("return false;",OPEN71_SCOPED)
        self.assertNotIn("ctx.mmu.write",OPEN71_SCOPED)
        self.assertNotIn("ipc70_ram.write",OPEN71_SCOPED)

    def test_callback_generator_aot_analysis_only(self):
        src=(HERE/"generate_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        result=derive_generator(src)
        self.assertIn(NEW_ROOTS,result)
        self.assertIn("V225_CB_ANALYZER rooted=1 analyzed=",result)
        self.assertIn("V232_CB_ANALYZER rooted=1 analyzed=",result)
        self.assertIn("funcs.count(0x8051e06cu)==1u",result)
        self.assertNotIn("V232_CB_ANALYZER",src)
    def test_no_guest_or_ios_mutation(self):
        for marker in ("scheduler.service_one(","ipc70_bus.write32(",
                       "ipc70_ram.write8(","ctx.mmu.write32("):
            self.assertEqual(self.before.count(marker),self.after.count(marker))
        for x in (CONTINUE,OBSERVER,NEXT_END):
            for forbidden in ("ipc70_bus.write","ipc70_ram.write",
                              "ctx.mmu.write","ctx.pc=0x"):
                self.assertNotIn(forbidden,x)
            self.assertNotRegex(x,r"ctx\.gpr\[[0-9]+\]\s*=(?!=)")
    def test_owner_16_trials_and_private_cleanup(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for marker in ("derive_v232_sc_isfs_callback_next_harness.py",
                       "derive_v225_isfs_callback_generator.py",
                       "V231_SC_Y1_ISFS_CALLBACK verified=1",
                       "V232_SC_ISFS_CALLBACK_NEXT verified=1"):
            self.assertIn(marker,script)
        good=("V232_ISFS_NEXT clear=1 wire=1 guest=1 sc=1 mapped=1 "
              "selected=1 from_isfs=1 nested=1 result=1 userdata=1 pc=8051e06c lr=804f0f54")
        self.assertNotIn("derive_v232_nand_callback_generator.py",script)
        self.assertNotIn("V232_NAND_CALLBACK_ROOT verified=1",script)
        self.assertIsNotNone(re.fullmatch(PASS,good))
        self.assertIsNone(re.fullmatch(PASS,good.replace("wire=1","wire=0")))
        self.assertIsNotNone(re.fullmatch(PATTERN,good.replace("nested=1","nested=0")))
        wf=(HERE.parents[1]/".github/workflows/wii-v232-sc-isfs-callback-next.yml").read_text()
        for marker in ("run_v232_sc_isfs_callback_next.sh",
                       "test_v232_sc_isfs_callback_next.py",
                       "V232_SC_ISFS_CALLBACK_NEXT verified=1"):
            self.assertIn(marker,wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)
        with tempfile.TemporaryDirectory() as d:
            for name,text in (("runner",script),
               ("wrapper",(HERE/"run_v232_sc_isfs_callback_next.sh").read_text())):
                p=Path(d)/name;p.write_text(text,encoding="utf-8")
                subprocess.run(["bash","-n",str(p)],check=True)
if __name__=="__main__":unittest.main()
