#!/usr/bin/env python3
"""V208 original-free second IOS reply publication at original guest yield."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v207_sc_y2_helper_next_harness import (
    derive as previous, OBSERVER as PREVIOUS_OBSERVER, NEXT_END as PREVIOUS_END,
)
from derive_v208_sc_y2_reply_publication_harness import derive, STOP, PUBLISH, NEXT_END, SEND
from derive_v208_sc_y2_reply_publication_runner import derive as runner, PATTERN, PASS, KIND, ARGS, MODE, SEND_PATTERN, STABLE_PATTERN, SWAP_PATTERN, LAYOUT_PATTERN, BASE_PATTERN
HERE=Path(__file__).resolve().parent

class V208(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=previous(source)
        cls.after=derive(source)

    def test_exact_original_second_yield_and_single_ios_pump(self):
        self.assertEqual(PREVIOUS_OBSERVER.count(STOP),1)
        self.assertNotIn(STOP,self.after)
        self.assertIn(PUBLISH,self.after)
        self.assertIn(NEXT_END,self.after)
        self.assertNotIn(PREVIOUS_END,self.after)
        for marker in ("addr==0x80529434u&&ctx.lr==0x80526cb0u",
                       "queued&&open&&!replied", "v183_second_phys",
                       "scheduler.service_one(ctx.msr)",
                       "service.progress==S::Pump::Replied",
                       "service.serviced_steps==1u",
                       "ipc70_ram.read32(req)==S::Reply",
                       "ipc70_ram.read32(req+8u)==S::Open",
                       "ipc70_bus.services().queued_replies()==0u",
                       "ctx.inst_count==inst_before",
                       "sc_before=ctx.mmu.read8(ctx.gpr[13]-3176u)==1u"):
            self.assertIn(marker,PUBLISH)
        self.assertEqual(self.after.count("scheduler.service_one("),
                         self.before.count("scheduler.service_one(")+1)
        self.assertEqual(PUBLISH.count("scheduler.service_one(ctx.msr)"),1)
        with self.assertRaises(ValueError):
            derive("unrecognized")

    def test_no_manual_guest_reply_irq_or_register_patch(self):
        for needle in ("ipc70_bus.tick(", "ipc70_bus.write32(",
                       "ipc70_ram.write8(","ctx.mmu.write32("):
            self.assertEqual(self.before.count(needle),self.after.count(needle))
        for segment in (PUBLISH,NEXT_END):
            for forbidden in ("ipc70_bus.write", "ipc70_ram.write",
                              "ipc70_bus.tick(","ctx.mmu.write"):
                self.assertNotIn(forbidden,segment)
        self.assertNotRegex(PUBLISH,
            r"\bctx\.(?:msr|pc|lr|srr0|srr1|gpr)\s*=(?!=)")

    def test_owner_sixteen_trial_gate_and_cleanup(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        self.assertIn("derive_v208_sc_y2_reply_publication_harness.py",script)
        self.assertIn("V207_SC_Y2_HELPER_NEXT verified=1",script)
        self.assertIn("V208_SC_Y2_REPLY_PUBLICATION verified=1",script)
        self.assertIn(')" -eq 16',script)
        good="V208_Y2_REPLY step=1 wire=1 opened=1 signal=1 drained=1 cpu=1 sc=1 pc=80529434 lr=80526cb0"
        self.assertIsNotNone(re.fullmatch(PASS,good))
        self.assertIsNotNone(re.fullmatch(PATTERN,good.replace("drained=1","drained=0")))
        self.assertIsNone(re.fullmatch(PASS,good.replace("wire=1","wire=0")))
        self.assertIsNotNone(re.fullmatch(
            KIND,"V208_Y2_KIND immediate=0 event=0 fs=0 file=0 es=0 negative=1 result=-106"))
        self.assertIsNotNone(re.fullmatch(
            KIND,"V208_Y2_KIND immediate=1 event=0 fs=0 file=0 es=0 negative=0 result=2"))
        self.assertIsNone(re.fullmatch(
            KIND,"V208_Y2_KIND immediate=0 event=0 fs=0 file=0 es=0 negative=1 result=/private"))
        kind="V208_Y2_KIND immediate=0 event=1 fs=0 file=0 es=0 negative=0 result=2"
        self.assertIsNotNone(re.fullmatch(KIND,kind))
        self.assertIsNone(re.fullmatch(KIND,kind+" path=/private"))
        self.assertIn("V208_Y2_KIND",script)
        self.assertIn("V208_Y2_OPEN_ARGS",script)
        self.assertIsNotNone(re.fullmatch(ARGS,
            "V208_Y2_OPEN_ARGS zero=1 mapped=0 mode_valid=1 mode_hi8=0 invalid=1"))
        self.assertIsNotNone(re.fullmatch(ARGS,
            "V208_Y2_OPEN_ARGS zero=0 mapped=1 mode_valid=0 mode_hi8=1 invalid=1"))
        self.assertIsNone(re.fullmatch(ARGS,
            "V208_Y2_OPEN_ARGS zero=0 mapped=/private mode_valid=0 mode_hi8=1 invalid=1"))
        probe="V208_Y2_MODE swap_valid=1 mem1virt=0 mem2virt=0 mem1phys=0 mem2phys=0 same_path=0 aligned=1 path_slash=1"
        self.assertIsNotNone(re.fullmatch(MODE,probe))
        self.assertIsNone(re.fullmatch(MODE,probe+" raw=0x1234"))
        self.assertIn("V208_Y2_MODE",script)
        self.assertIn("swapped_mode",PUBLISH)
        self.assertNotIn("<<mode_arg",PUBLISH)
        self.assertNotIn("<<swapped_mode",PUBLISH)
        self.assertIn("v183_second_phys=value;",SEND)
        self.assertIn("ipc70_ram.read32(value+16u)",SEND)
        self.assertIn("V208_Y2_SEND",SEND)
        self.assertIn("V208_Y2_STABLE",PUBLISH)
        send="V208_Y2_SEND witness=1 ptr=1 slash=0 mode_valid=0 mode_mem2=1"
        stable="V208_Y2_STABLE sent=1 path=1 mode=1"
        self.assertIsNotNone(re.fullmatch(SEND_PATTERN,send))
        self.assertIsNotNone(re.fullmatch(STABLE_PATTERN,stable))
        self.assertIsNone(re.fullmatch(STABLE_PATTERN,stable+" data=/secret"))
        self.assertIn("V208_Y2_SEND",script)
        self.assertIn("V208_Y2_STABLE",script)
        self.assertNotIn("<<a<<",SEND)
        self.assertNotIn("<<b<<",SEND)
        swapped="V208_Y2_SWAP path_mode=1 mode_mem2=1 mode_mapped=1 mode_slash=1 mode_string=1"
        self.assertIsNotNone(re.fullmatch(SWAP_PATTERN,swapped))
        self.assertIsNone(re.fullmatch(SWAP_PATTERN,swapped+" raw=private"))
        self.assertIn("V208_Y2_SWAP",PUBLISH)
        self.assertIn("mode_arg&0x1fffffffu",PUBLISH)
        self.assertIn("i<64u",PUBLISH)
        self.assertNotIn("<<mode_as_phys",PUBLISH)
        layout="V208_Y2_LAYOUT ptr0c=0 ptr10=1 ptr14=0 ptr18=0 ptr1c=0 mode0c=0 mode10=0 mode14=1 mode18=0 mode1c=0"
        self.assertIsNotNone(re.fullmatch(LAYOUT_PATTERN,layout))
        self.assertIsNone(re.fullmatch(LAYOUT_PATTERN,layout+" secret=1"))
        self.assertIn("V208_Y2_LAYOUT",PUBLISH)
        self.assertIn("read32(req+20u)",PUBLISH)
        self.assertIn("read32(req+24u)",PUBLISH)
        self.assertIn("read32(req+28u)",PUBLISH)
        self.assertIn("i<64u",PUBLISH)
        self.assertNotIn("<<alt14",PUBLISH)
        self.assertNotIn("<<alt18",PUBLISH)
        self.assertNotIn("<<alt1c",PUBLISH)
        base="V208_Y2_BASE old_valid=1 old_reply=1 old_path=1 old_mode=1 old_open=1 same_ptr=0"
        self.assertIsNotNone(re.fullmatch(BASE_PATTERN,base))
        self.assertIsNone(re.fullmatch(BASE_PATTERN,base+" guest=/private"))
        self.assertIn("V208_Y2_BASE",PUBLISH)
        self.assertIn("read32(v153_phys+12u)",PUBLISH)
        self.assertIn("read32(v153_phys+16u)",PUBLISH)
        self.assertIn("services().is_open(v153_fd",PUBLISH)
        self.assertNotIn("<<first_path<<",PUBLISH)
        self.assertNotIn("<<first_mode<<",PUBLISH)
        wf=(HERE.parents[1]/".github/workflows/wii-v208-sc-y2-reply-publication.yml").read_text()
        for needle in ("run_v208_sc_y2_reply_publication.sh",
                       "test_v208_sc_y2_reply_publication.py",
                       "V208_SC_Y2_REPLY_PUBLICATION verified=1"):
            self.assertIn(needle,wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)
        with tempfile.TemporaryDirectory() as d:
            for name,content in (
                ("runner.sh",script),
                ("entry.sh",(HERE/"run_v208_sc_y2_reply_publication.sh").read_text())):
                p=Path(d)/name;p.write_text(content,encoding="utf-8")
                subprocess.run(["bash","-n",str(p)],check=True)

if __name__=="__main__":
    unittest.main()
