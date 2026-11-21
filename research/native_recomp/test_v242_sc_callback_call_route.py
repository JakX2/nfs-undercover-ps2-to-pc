#!/usr/bin/env python3
"""V242 original-free callback-to-malformed ISFS call route regression."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v242_sc_callback_call_route_harness import derive, TRACE, SEND, NEXT_EXTRA
from derive_v242_sc_callback_call_route_runner import derive as runner, TRACE as TRACE_REGEX, PATTERN, PASS
from derive_v241_sc_first_callback_dispatch_harness import derive as previous, TRACE as PREVIOUS_TRACE
HERE=Path(__file__).resolve().parent
class V242(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        s=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=previous(s);cls.after=derive(s)
    def test_original_wii_callback_path_observer(self):
        for marker in ("v241_cb_count>0u","v183_second_phys==0u",
                       "v242_count<24u","addr==0x804f0e04u",
                       "addr==0x804f1e2cu","ctx.lr==0x805192acu",
                       "V242_TRACE"):
            self.assertIn(marker,TRACE)
        for marker in ("V242_ROUTE","v242_count>0u",
                       "v239_return_pc==0x805192acu",
                       "++v242_submit_seen"):
            self.assertIn(marker,SEND)
        self.assertIn(PREVIOUS_TRACE+TRACE,self.after)
        self.assertIn(NEXT_EXTRA,self.after)
        with self.assertRaises(ValueError):derive("unexpected")
    def test_no_guest_or_native_ios_state_changes(self):
        for marker in ("ipc70_bus.write32(","ipc70_ram.write8(",
                       "ctx.mmu.write32(","scheduler.service_one("):
            self.assertEqual(self.before.count(marker),self.after.count(marker))
        for part in (TRACE,SEND):
            for bad in ("ipc70_bus.write","ipc70_ram.write","ctx.mmu.write",
                        "<<ctx.gpr","<<ctx.ctr","<<ctx.mmu","<<v183_second_phys"):
                self.assertNotIn(bad,part)
            self.assertNotRegex(part,r"ctx\.gpr\[[0-9]+\]\s*=(?!=)")
    def test_16_trials_workflow_and_private_cleanup(self):
        s=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for marker in ("derive_v242_sc_callback_call_route_harness.py",
                       "V241_SC_FIRST_CALLBACK_DISPATCH verified=1",
                       "V242_SC_CALLBACK_CALL_ROUTE verified=1"):
            self.assertIn(marker,s)
        row="V242_ROUTE count=8 cb=1 isfs_entry=0 handler_lr=1 captured=1 second=1 last_pc=8051982c last_lr=804f1ecc"
        self.assertIsNotNone(re.fullmatch(PASS,row))
        self.assertIsNone(re.fullmatch(PASS,row.replace("second=1","second=0")))
        self.assertIsNotNone(re.fullmatch(TRACE_REGEX,"V242_TRACE seq=3 cb=0 isfs=0 ipc=1 lr_text=1 handler_lr=0 pc=80519094 lr=804f1e60"))
        wf=(HERE.parents[1]/".github/workflows/wii-v242-sc-callback-call-route.yml").read_text()
        for marker in ("run_v242_sc_callback_call_route.sh",
                       "test_v242_sc_callback_call_route.py",
                       "V242_SC_CALLBACK_CALL_ROUTE verified=1"):
            self.assertIn(marker,wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)
        with tempfile.TemporaryDirectory() as temp:
            for name,content in (("runner",s),("wrapper",(HERE/"run_v242_sc_callback_call_route.sh").read_text())):
                p=Path(temp)/name;p.write_text(content)
                subprocess.run(["bash","-n",str(p)],check=True)
if __name__=="__main__":
    unittest.main()
