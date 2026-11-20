#!/usr/bin/env python3
"""V183 bounded authentic Wii SC IPC guest call trace source-only validation."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v182_sc_reply_burst_harness import derive as previous
from derive_v183_sc_reply_burst_harness import (
    derive, STOP, CONTINUE, OBSERVER, PAIR, NEXT_TRIAL, MAX_CALLS,
    PREVIOUS_OBSERVER, widen_prior,
    V77_IRQ_CATCHALL, V183_IRQ_DIAGNOSTIC,
)
from derive_v183_sc_reply_burst_runner import derive as runner, PASS, TRACE, DEP

HERE=Path(__file__).resolve().parent

class V183(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=previous(base)
        cls.after=derive(base)

    def test_resume_exact_v182_original_ipc_sender_function(self):
        self.assertEqual(MAX_CALLS,8)
        self.assertIn(STOP,PREVIOUS_OBSERVER)
        self.assertIn(STOP,self.before)
        self.assertNotIn(STOP,self.after)
        self.assertIn(CONTINUE,self.after)
        self.assertIn("addr==0x8051906cu&&ctx.lr==0x80519780u",CONTINUE)
        self.assertIn("v182_calls==8u&&v182_status_before==1u",CONTINUE)
        self.assertIn("return; // execute original Wii 0x8051906C",CONTINUE)
        self.assertIn("v182_burst_seen==1u&&v183_burst_seen==0u",OBSERVER)
        self.assertIn("v183_calls<8u&&!changed",OBSERVER)
        self.assertIn("v183_last_inst=ctx.inst_count",OBSERVER)
        self.assertIn(NEXT_TRIAL,self.after)

    def test_no_guest_or_ios_writes_and_inherited_vector_proofs_preserved(self):
        for token in ("ctx.mmu.write8(", "ctx.mmu.write16(", "ctx.mmu.write32(",
                      "ipc70_ram.write8(", "ipc70_bus.write32(",
                      "scheduler.service_one(ctx.msr)", "ipc70_bus.tick("):
            self.assertEqual(self.before.count(token),self.after.count(token),token)
        for tag in ("V182_SC_BURST calls=", "V182_REQUEST_SC guest=1",
                    "V182_CACHE_SC guest=1", "V182_CACHE_VECTOR entered=1",
                    "V181_SC_NEXT clean=", "V179_SC_NEXT clean="):
            self.assertEqual(self.before.count(tag),self.after.count(tag),tag)
        self.assertNotIn("ctx.mmu.write",OBSERVER)
        self.assertNotIn("ipc70_bus.write",OBSERVER)
        self.assertNotIn("scheduler.service_one",OBSERVER)

    def test_historical_irq_dispatch_fallback_is_diagnostic_only(self):
        self.assertEqual(self.before.count(V77_IRQ_CATCHALL),1)
        self.assertEqual(self.after.count(V183_IRQ_DIAGNOSTIC),1)
        self.assertEqual(
            self.before.count("unexpected original IRQ dispatcher dependency"),
            self.after.count("unexpected original IRQ dispatcher dependency"))
        self.assertIn("v182_burst_seen==1u&&v183_burst_seen==0u",V183_IRQ_DIAGNOSTIC)
        self.assertIn('check(false,"unexpected original IRQ dispatcher dependency");',
                      V183_IRQ_DIAGNOSTIC)
        self.assertTrue(re.fullmatch(
            DEP,"V183_IRQ_DEP phase=1 submit=1 dispatch=1 ipc=1 prior=1 "
                "tracked=1 masked=1 mapped=1 status=1 calls=0 "
                "pc=8051905c lr=805197a0"))
        self.assertFalse(re.fullmatch(
            DEP,"V183_IRQ_DEP phase=1 submit=1 dispatch=1 ipc=1 prior=1 "
                "tracked=1 masked=1 mapped=1 status=1 calls=9 "
                "pc=8051905c lr=805197a0"))
        self.assertNotIn("ctx.mmu.write",V183_IRQ_DIAGNOSTIC)

    def test_prior_authenticated_pc_lr_endpoints_accept_new_native_stop(self):
        self.assertGreaterEqual(len(PAIR.findall(self.before)),7)
        self.assertEqual(len(PAIR.findall(self.before)),len(PAIR.findall(self.after)))
        for marker in ("V178 original SC reply burst did not reach bounded native checkpoint",
                       "V181 original SC reply successor did not reach another native function",
                       "V182 original SC reply call burst did not reach authenticated native stop"):
            end=self.after.index('"'+marker+'");')
            start=self.after.rfind("check(",0,end)
            self.assertIn("v183_burst_seen==1u",self.after[start:end])
        with self.assertRaises(ValueError):derive("invalid")
        with self.assertRaises(ValueError):widen_prior("invalid")

    def test_runner_sixteen_owner_trials_and_private_cleanup(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text(encoding="utf-8"))
        self.assertIn("derive_v183_sc_reply_burst_harness.py",script)
        self.assertIn("V182_SC_BURST verified=1",script)
        self.assertIn("V183_SC_BURST verified=1",script)
        self.assertIn('trap \'rm -rf -- "$work"\' EXIT',script)
        good=("V183_SC_BURST calls=8 clean=1 reply=1 queue=1 guest=1 "
              "caller=1 coherent=1 mapped=1 before=1 status=1 changed=0 "
              "pc=8051905c lr=805197a0")
        self.assertTrue(re.fullmatch(PASS,good))
        self.assertTrue(re.fullmatch(PASS,good.replace("calls=8","calls=2").replace("status=1 changed=0","status=0 changed=1")))
        self.assertFalse(re.fullmatch(PASS,good.replace("calls=8","calls=9")))
        self.assertTrue(re.fullmatch(TRACE,"V183_SC_TRACE step=8 pc=8051905c lr=805197a0"))
        with tempfile.TemporaryDirectory() as root:
            sh=Path(root)/"runner.sh";sh.write_text(script,encoding="utf-8")
            subprocess.run(["bash","-n",str(sh)],check=True)

    def test_owner_ci_keeps_private_source_unpublished(self):
        wf=(HERE.parents[1]/".github/workflows/wii-v183-sc-reply-burst.yml").read_text(encoding="utf-8")
        self.assertIn("run_v183_sc_reply_burst.sh",wf)
        self.assertIn("V183_SC_BURST verified=1",wf)
        self.assertIn("  cancel-in-progress: false",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)

if __name__=="__main__":
    unittest.main()
