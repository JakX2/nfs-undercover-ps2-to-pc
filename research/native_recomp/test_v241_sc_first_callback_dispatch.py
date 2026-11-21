#!/usr/bin/env python3
"""Original-free V241 callback entry observation test."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v241_sc_first_callback_dispatch_harness import derive, TRACE, SEND, NEXT_EXTRA, TRACE_ANCHOR
from derive_v241_sc_first_callback_dispatch_runner import derive as runner, ENTRY, PATTERN, PASS
from derive_v240_sc_first_callback_abi_harness import derive as previous
HERE=Path(__file__).resolve().parent

class V241(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        s=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=previous(s);cls.after=derive(s)
    def test_native_wii_callback_entry(self):
        for marker in ("ctx.pc==addr&&addr==0x804f0e04u",
                       "ipc70_ram.read32(v153_phys+32u)",
                       "ctx.gpr[3]==v241_result",
                       "ctx.gpr[4]==v241_user",
                       "ctx.ctr==v241_target","V241_CB_ENTRY"):
            self.assertIn(marker,TRACE)
        for marker in ("V241_DISPATCH","v241_cb_count>0u",
                       "v240_cb_isfsfunc&&v240_ctr_cb",
                       "g_trace_calls","++v241_submit_seen"):
            self.assertIn(marker,SEND)
        self.assertIn(TRACE_ANCHOR+"\n"+TRACE,self.after)
        self.assertIn(NEXT_EXTRA,self.after)
        with self.assertRaises(ValueError):derive("invalid")
    def test_only_read_guest_and_original_callback(self):
        for s in ("ipc70_bus.write32(","ipc70_ram.write8(",
                  "ctx.mmu.write32(","scheduler.service_one("):
            self.assertEqual(self.before.count(s),self.after.count(s))
        for part in (TRACE,SEND):
            for forbidden in ("ipc70_bus.write","ipc70_ram.write",
                              "ctx.mmu.write","<<v241_target","<<v241_result",
                              "<<v241_user"):
                self.assertNotIn(forbidden,part)
            self.assertNotRegex(part,r"ctx\.gpr\[[0-9]+\]\s*=(?!=)")
    def test_owner_trials_workflow_cleanup(self):
        s=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for marker in ("derive_v241_sc_first_callback_dispatch_harness.py",
                       "V240_SC_FIRST_CALLBACK verified=1",
                       "V241_SC_FIRST_CALLBACK_DISPATCH verified=1"):
            self.assertIn(marker,s)
        line="V241_DISPATCH cb_count=0 traced=0 registered=1 trace_enabled=1 lr_ok=0 target_ok=0 abi_ok=0 ctr_ok=0 second_invalid=1 first_reply=1"
        self.assertIsNotNone(re.fullmatch(PASS,line))
        self.assertIsNone(re.fullmatch(PASS,line.replace("registered=1","registered=0")))
        self.assertIsNotNone(re.fullmatch(ENTRY,"V241_CB_ENTRY seq=1 lr=1 target=1 abi=1 ctr=1"))
        wf=(HERE.parents[1]/".github/workflows/wii-v241-sc-first-callback-dispatch.yml").read_text()
        for name in ("run_v241_sc_first_callback_dispatch.sh",
                     "test_v241_sc_first_callback_dispatch.py",
                     "V241_SC_FIRST_CALLBACK_DISPATCH verified=1"):
            self.assertIn(name,wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)
        with tempfile.TemporaryDirectory() as td:
            for name,code in (("runner",s),("wrapper",(HERE/"run_v241_sc_first_callback_dispatch.sh").read_text())):
                p=Path(td)/name;p.write_text(code)
                subprocess.run(["bash","-n",str(p)],check=True)

if __name__=="__main__":
    unittest.main()
