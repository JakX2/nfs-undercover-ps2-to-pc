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
from derive_v208_sc_y2_reply_publication_harness import derive, STOP, PUBLISH, NEXT_END, SEND, TRACE_HOOK
from derive_v208_sc_y2_reply_publication_runner import derive as runner, PATTERN, PASS, KIND, ARGS, MODE, SEND_PATTERN, STABLE_PATTERN, SWAP_PATTERN, LAYOUT_PATTERN, BASE_PATTERN, ORIGIN_PATTERN, PATHCLASS_PATTERN, ASYNC_PATTERN, ASYNC_LINK_PATTERN, ISFS_PATTERN, ISFS_TO_IOS_PATTERN, PROLOGUE_PATTERN, GPR_FLOW_PATTERN, PROVENANCE_PATTERN, CALLER_PATTERN, CALLBACK_PATTERN, CALLBACK_CLASS_PATTERN, CALLBACK_ENTRY_PATTERN, CALLBACK_FLOW_PATTERN
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
        entry=("V208_Y2_ASYNC_ENTRY seen=1 tracked=1 pathmap=1 "
               "pathslash=0 modevalid=0 modemem2=1 modeslash=1 lr=8052f000")
        link="V208_Y2_ASYNC_LINK witnessed=1 path_same=1 mode_same=1 path_is_mode=0 mode_is_path=0"
        self.assertIsNotNone(re.fullmatch(ASYNC_PATTERN,entry))
        self.assertIsNotNone(re.fullmatch(ASYNC_LINK_PATTERN,link))
        self.assertIsNone(re.fullmatch(ASYNC_PATTERN,entry+" ptr=private"))
        self.assertIn("addr==0x8051982cu",TRACE_HOOK)
        self.assertIn("ctx.gpr[3],mode=ctx.gpr[4]",TRACE_HOOK)
        self.assertIn("V208_Y2_ASYNC_ENTRY",TRACE_HOOK)
        # Trace observers are chained: do not swallow V179's native
        # guest-call checks when the IOS_OpenAsync entry is observed.
        self.assertNotIn("return;",TRACE_HOOK)
        self.assertIn("Preserve inherited trace observers",TRACE_HOOK)
        self.assertIn("V208_Y2_ASYNC_LINK",SEND)
        self.assertIn("v208_async_mode",SEND)
        self.assertIn("v208_async_path&0x1fffffffu",SEND)
        self.assertNotIn("ipc70_ram.write",TRACE_HOOK)
        self.assertNotIn("ctx.mmu.write",TRACE_HOOK)
        self.assertIn("V208_Y2_ASYNC_ENTRY",script)
        self.assertIn("V208_Y2_ASYNC_LINK",script)
        isfs=("V208_Y2_ISFS_ENTRY seen=1 count=2 nand=1 logging=0 mapped=1 "
              "slash=1 modevalid=1 modemem2=0 modeslash=0")
        bridge=("V208_Y2_ISFS_TO_IOS witnessed=1 mode=1 copy=1 "
                "source_slash=1 dest_slash=1 modevalid=1")
        self.assertIsNotNone(re.fullmatch(ISFS_PATTERN,isfs))
        self.assertIsNotNone(re.fullmatch(ISFS_TO_IOS_PATTERN,bridge))
        self.assertIsNone(re.fullmatch(ISFS_PATTERN,isfs+" private=/shared2"))
        self.assertIn("v208_isfs_seen<32u",TRACE_HOOK)
        self.assertIn("ctx.inst_count>v208_isfs_inst",TRACE_HOOK)
        self.assertIn("if(v208_async_seen==0u&&v183_second_msg==0u&&",TRACE_HOOK)
        for marker in ("addr==0x804f1e2cu","v208_isfs_path=path",
                       "ctx.lr==0x8051de3cu","ctx.lr==0x8051f700u",
                       "V208_Y2_ISFS_ENTRY","V208_Y2_ISFS_TO_IOS",
                       "v208_isfs_path+i","copied=copied&&terminated"):
            self.assertIn(marker,TRACE_HOOK)
        self.assertNotIn("return;",TRACE_HOOK)
        self.assertNotIn("ctx.mmu.write",TRACE_HOOK)
        self.assertNotIn("<<path<<",TRACE_HOOK)
        self.assertNotIn("<<v208_isfs_path",TRACE_HOOK)
        self.assertIn("V208_Y2_ISFS_ENTRY",script)
        self.assertIn("V208_Y2_ISFS_TO_IOS",script)
        self.assertIn("V208_Y2_PROLOGUE",TRACE_HOOK)
        self.assertIn("addr==0x80545100u",TRACE_HOOK)
        self.assertIn("ctx.lr==0x804f1e40u",TRACE_HOOK)
        self.assertIn("V208_Y2_GPR_FLOW",TRACE_HOOK)
        self.assertIn("v208_prologue_inst=ctx.inst_count",TRACE_HOOK)
        self.assertNotIn("ctx.mmu.write",TRACE_HOOK)
        initial="V208_Y2_PROLOGUE seen=1 mapped=1 slash=1 mode_valid=1 mode_mem2=0 mode_slash=0"
        flow="V208_Y2_GPR_FLOW witnessed=1 mode_same=0 first_valid=1 ios_valid=0 first_slash=1 ios_slash=0"
        self.assertIsNotNone(re.fullmatch(PROLOGUE_PATTERN,initial))
        self.assertIsNotNone(re.fullmatch(GPR_FLOW_PATTERN,flow))
        self.assertIsNone(re.fullmatch(GPR_FLOW_PATTERN,flow+" private=/dev/test"))
        self.assertIn("V208_Y2_PROLOGUE",script)
        self.assertIn("V208_Y2_GPR_FLOW",script)
        provenance=("V208_Y2_PROVENANCE saved=1 nand=1 log=0 other=0 "
                    "path_stack=1 stack_slash=1 r31_scalar=1 r4_eq_r31=1")
        self.assertIn("V208_Y2_PROVENANCE",TRACE_HOOK)
        self.assertIn("ctx.mmu.read32(sp+36u)",TRACE_HOOK)
        self.assertIn("source_lr==0x8051de3cu",TRACE_HOOK)
        self.assertIn("p==sp+40u",TRACE_HOOK)
        self.assertIn("m==ctx.gpr[31]",TRACE_HOOK)
        self.assertIsNotNone(re.fullmatch(PROVENANCE_PATTERN,provenance))
        self.assertIsNone(re.fullmatch(PROVENANCE_PATTERN,provenance+" addr=private"))
        self.assertIn("V208_Y2_PROVENANCE",script)
        self.assertIn("ctx.gpr[11]==sp+32u",TRACE_HOOK)
        self.assertIn("(text&&aligned?source_lr:0u)",TRACE_HOOK)
        self.assertNotIn("<<sp<<",TRACE_HOOK)
        caller="V208_Y2_CALLER text=1 aligned=1 frame=1 pc=8051de3c"
        self.assertIsNotNone(re.fullmatch(CALLER_PATTERN,caller))
        self.assertIsNone(re.fullmatch(CALLER_PATTERN,caller+" data=/private"))
        self.assertIn("V208_Y2_CALLER",script)
        # Verify only original-free booleans. The live guest request,
        # pointers, callback address and filename must never be logged.
        callback=("V208_Y2_CB_ABI return=1 parent=1 target=1 ctr=1 "
                  "result=1 userdata=1 reply=1 open=1 r3ptr=0 r4path=1")
        self.assertIsNotNone(re.fullmatch(CALLBACK_PATTERN,callback))
        self.assertIsNone(re.fullmatch(CALLBACK_PATTERN,callback+" path=/private"))
        self.assertIn("V208_Y2_CB_ABI",TRACE_HOOK)
        self.assertIn("source_lr==0x805192acu",TRACE_HOOK)
        self.assertIn("ctx.mmu.read32(parent+32u)",TRACE_HOOK)
        self.assertIn("ctx.mmu.read32(parent+36u)",TRACE_HOOK)
        self.assertIn("ctx.gpr[3]==ctx.mmu.read32(parent+4u)",TRACE_HOOK)
        self.assertNotRegex(TRACE_HOOK,r"<<\\s*parent\\b")
        self.assertNotRegex(TRACE_HOOK,r"<<\\s*callback\\b")
        self.assertNotIn("ctx.mmu.write",TRACE_HOOK)
        self.assertIn("V208_Y2_CB_ABI",script)
        classified=("V208_Y2_CB_CLASS text=1 physical=0 isfs=0 isfs_cb=1 "
                    "ctr_text=1 ctr_isfs_cb=1 same_ctr=1 first=1 second=0 user_mem2=1")
        self.assertIsNotNone(re.fullmatch(CALLBACK_CLASS_PATTERN,classified))
        self.assertIsNone(re.fullmatch(CALLBACK_CLASS_PATTERN,classified+" callback=private"))
        self.assertIn("V208_Y2_CB_CLASS",TRACE_HOOK)
        self.assertIn("callback==0x804f0e04u",TRACE_HOOK)
        self.assertIn("parent==(v153_phys|0x80000000u)",TRACE_HOOK)
        self.assertNotRegex(TRACE_HOOK,r"<<\s*callback\b")
        self.assertNotRegex(TRACE_HOOK,r"<<\s*parent\b")
        self.assertIn("V208_Y2_CB_CLASS",script)
        cb_entry="V208_Y2_CB_ENTRY caller=1 ctr=1 first=1 result=1 userdata=1 guest=1"
        cb_flow=("V208_Y2_CB_FLOW inner=1 advanced=1 callback_site=1 "
                 "reply_site=0 saved_r0=1 r0_cb=1 r0_reply=0")
        self.assertIsNotNone(re.fullmatch(CALLBACK_ENTRY_PATTERN,cb_entry))
        self.assertIsNotNone(re.fullmatch(CALLBACK_FLOW_PATTERN,cb_flow))
        self.assertIsNone(re.fullmatch(CALLBACK_FLOW_PATTERN,cb_flow+" path=/private"))
        self.assertIn("addr==0x804f0e04u",TRACE_HOOK)
        self.assertIn("ctx.gpr[0]==source_lr",TRACE_HOOK)
        self.assertIn("v208_isfs_cb_entry==1u",TRACE_HOOK)
        self.assertIn("V208_Y2_CB_ENTRY",TRACE_HOOK)
        self.assertIn("V208_Y2_CB_FLOW",TRACE_HOOK)
        self.assertIn("V208_Y2_CB_ENTRY",script)
        self.assertIn("V208_Y2_CB_FLOW",script)
        origin=("V208_Y2_ORIGIN pc_text=1 lr_text=1 mem1=1 mem2=0 reused=0 overlap=0 "
                "a_block=1 a_open=0 a_reply=0 req_regs=4 path_regs=2 pc=8051906c lr=805192c8")
        pathcls=("V208_Y2_PATHCLASS valid=1 dev=1 stm=1 fs=0 es=0 "
                 "shared2=0 sysconf=0 title=0")
        self.assertIsNotNone(re.fullmatch(ORIGIN_PATTERN,origin))
        self.assertIsNotNone(re.fullmatch(PATHCLASS_PATTERN,pathcls))
        self.assertIsNone(re.fullmatch(PATHCLASS_PATTERN,pathcls+" raw=/private"))
        self.assertIn("V208_Y2_ORIGIN",SEND)
        self.assertIn("V208_Y2_PATHCLASS",SEND)
        self.assertIn("ipc70_ram.cpu",SEND)
        self.assertIn("value==v153_phys",SEND)
        self.assertIn("candidate==",SEND)
        self.assertNotIn('<<candidate',SEND)
        self.assertNotIn('<<bphys',SEND)
        self.assertNotIn('<<value',SEND)
        self.assertIn("V208_Y2_ORIGIN",script)
        self.assertIn("V208_Y2_PATHCLASS",script)

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
