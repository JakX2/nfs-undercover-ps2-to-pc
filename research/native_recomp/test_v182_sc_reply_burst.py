#!/usr/bin/env python3
"""V182 original-free eight-call SC reply burst and safety regression."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v181_sc_reply_next_harness import derive as previous
from derive_v182_sc_reply_burst_harness import (
    derive, STOP, CONTINUE, OBSERVER, PAIR, NEXT_TRIAL, MAX_CALLS,
    V112_SYSCALL_GUARD, V182_V112_TELEMETRY,
    V112_SYSCALL_DISPATCH, V182_SYSCALL_SCOPED,
    BASE_SC_FALLBACK, V182_SC_FALLBACK, V182_NATIVE_CACHE_SC,
    V182_VECTOR_OBSERVER, V114_SYSCALL_ASSERTION, V182_V114_DIAGNOSTIC,
    PREVIOUS_FOLLOWUP, widen_prior,
)
from derive_v182_sc_reply_burst_runner import derive as runner, PASS, TRACE, DEP, FALLBACK, CACHE, PRE, AFTER, VECTOR, V114

HERE=Path(__file__).resolve().parent

class V182(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=previous(base)
        cls.after=derive(base)

    def test_execute_verified_second_allocator_successor(self):
        self.assertEqual(MAX_CALLS,8)
        self.assertIn(STOP,PREVIOUS_FOLLOWUP)
        self.assertIn(STOP,self.before)
        self.assertNotIn(STOP,self.after)
        self.assertIn(CONTINUE,self.after)
        self.assertIn("addr==0x8051ab34u&&ctx.lr==0x80519874u",CONTINUE)
        self.assertIn("v181_status_before==1u&&status==1u&&!changed",CONTINUE)
        self.assertIn("return; // execute authentic 0x8051AB34",CONTINUE)
        self.assertIn("v181_next_seen==1u&&v182_burst_seen==0u",OBSERVER)
        self.assertIn("v182_calls<8u&&!changed",OBSERVER)
        self.assertIn("v182_last_inst=ctx.inst_count",OBSERVER)
        self.assertIn(NEXT_TRIAL,self.after)

    def test_native_guest_state_and_prior_proofs_preserved(self):
        for token in ("ctx.mmu.write8(", "ctx.mmu.write16(", "ctx.mmu.write32(",
                      "ipc70_ram.write8(", "ipc70_bus.write32(",
                      "scheduler.service_one(ctx.msr)", "ipc70_bus.tick("):
            self.assertEqual(self.before.count(token),self.after.count(token),token)
        for tag in ("V178_SC_BURST calls=", "V179_SC_NEXT clean=",
                    "V180_SC_NEXT clean=", "V181_SC_NEXT clean="):
            self.assertEqual(self.before.count(tag),self.after.count(tag),tag)
        self.assertNotIn("ctx.mmu.write",OBSERVER)
        self.assertNotIn("ipc70_bus.write",OBSERVER)
        self.assertNotIn("scheduler.service_one",OBSERVER)

    def test_late_v114_request_flush_reports_state_without_bypassing_assertion(self):
        self.assertEqual(self.before.count(V114_SYSCALL_ASSERTION),1)
        self.assertEqual(self.after.count(V182_V114_DIAGNOSTIC),1)
        self.assertIn("v181_next_seen==1u&&v182_burst_seen==0u",V182_V114_DIAGNOSTIC)
        self.assertIn('check(route&&flushed&&abi&&prior,"V114 original IOS request flush syscall ABI differs");',
                      V182_V114_DIAGNOSTIC)
        self.assertTrue(re.fullmatch(
            V114,"V182_V114_DEP phase=1 syscall=1 flush=1 cache=1 calls=3 "
                 "route=0 flushed=0 abi=1 prior=1 pc=805222e8 lr=8051963c"))
        self.assertEqual(self.before.count("V114 original IOS request flush syscall ABI differs"),
                         self.after.count("V114 original IOS request flush syscall ABI differs"))
        self.assertNotIn("ctx.mmu.write",V182_V114_DIAGNOSTIC)

    def test_late_authentic_vector_execution_is_phase_scoped(self):
        self.assertIn("v182_cache_active&&addr==SYSCALL_DEST",V182_VECTOR_OBSERVER)
        self.assertIn("ctx.srr0==0x805222ecu&&ctx.lr==0x80519904u",V182_VECTOR_OBSERVER)
        self.assertIn("v182_cache_vector_seen==0u",V182_VECTOR_OBSERVER)
        self.assertIn("return; // original translated syscall vector executes unchanged",
                      V182_VECTOR_OBSERVER)
        self.assertIn(V182_VECTOR_OBSERVER,self.after)
        self.assertTrue(re.fullmatch(
            VECTOR,"V182_CACHE_VECTOR entered=1 resume=1 masked=1 pc=80000c00 lr=80519904"))
        self.assertFalse(re.fullmatch(
            VECTOR,"V182_CACHE_VECTOR entered=0 resume=1 masked=1 pc=80000c00 lr=80519904"))
        self.assertNotIn("ctx.mmu.write",V182_VECTOR_OBSERVER)
        self.assertNotIn("ipc70_bus.write",V182_VECTOR_OBSERVER)

    def test_late_cache_syscall_executes_original_vector_and_preserves_abi(self):
        self.assertIn("ctx.pc==0x805222e8u&&ctx.lr==0x80519904u",V182_NATIVE_CACHE_SC)
        self.assertIn("v181_next_seen==1u&&v182_burst_seen==0u",V182_NATIVE_CACHE_SC)
        self.assertIn("v182_cache_sc==0u&&v182_calls==3u",V182_NATIVE_CACHE_SC)
        self.assertIn("post112_sc==1u&&post112_vector==1u&&post112_flush==1u",V182_NATIVE_CACHE_SC)
        self.assertIn("native_idle_cache_sc(ctx,SYSCALL_DEST,sc_vector",V182_NATIVE_CACHE_SC)
        self.assertIn("[](auto& c){func_80000C00(c);}",V182_NATIVE_CACHE_SC)
        self.assertIn("ctx.pc==pc+4u&&ctx.msr==msr&&ctx.lr==lr",V182_NATIVE_CACHE_SC)
        self.assertIn("++v182_cache_sc;",V182_NATIVE_CACHE_SC)
        self.assertIn("unsigned(ctx.mmu.read8(ctx.gpr[13]-3176u))",V182_NATIVE_CACHE_SC)
        self.assertIn("v182_cache_active=true;",V182_NATIVE_CACHE_SC)
        self.assertIn("v182_cache_active=false;",V182_NATIVE_CACHE_SC)
        self.assertIn("v182_cache_vector_seen==1u",V182_NATIVE_CACHE_SC)
        self.assertIn("V182_CACHE_PRE phase=1",V182_NATIVE_CACHE_SC)
        self.assertIn("V182_CACHE_AFTER pcok=",V182_NATIVE_CACHE_SC)
        self.assertTrue(re.fullmatch(
            PRE,"V182_CACHE_PRE phase=1 calls=3 sc=1 vector=1 flush=1 lines=1 "
                "hid4=1 ee=1 pc=805222e8 lr=80519904"))
        self.assertTrue(re.fullmatch(
            AFTER,"V182_CACHE_AFTER pcok=1 msr=1 lr=1 hid0=1 hid4=1 ctr=1"))
        self.assertIn("return true;",V182_NATIVE_CACHE_SC)
        self.assertEqual(self.after.count(V182_NATIVE_CACHE_SC),1)
        self.assertTrue(re.fullmatch(
            CACHE,"V182_CACHE_SC guest=1 vector=1 sc=1 status=1 pc=805222e8 lr=80519904"))
        for forbidden in ("ctx.mmu.write8(", "ctx.mmu.write16(", "ctx.mmu.write32(",
                          "ipc70_bus.write32(", "scheduler.service_one(", "ipc70_bus.tick("):
            self.assertNotIn(forbidden,V182_NATIVE_CACHE_SC)

    def test_first_v112_syscall_only_and_late_cache_fallback_diagnostic(self):
        self.assertEqual(self.before.count(V112_SYSCALL_DISPATCH),1)
        self.assertEqual(self.after.count(V182_SYSCALL_SCOPED),1)
        self.assertNotIn(V112_SYSCALL_DISPATCH,self.after)
        self.assertIn("post112_sc==0u",V182_SYSCALL_SCOPED)
        self.assertIn("ctx.pc==0x805222e8u&&ctx.lr==0x80519904u",V182_SYSCALL_SCOPED)
        self.assertEqual(self.before.count(BASE_SC_FALLBACK),1)
        self.assertEqual(self.after.count(V182_SC_FALLBACK),1)
        self.assertIn("V182_SC_FALLBACK phase=1",V182_SC_FALLBACK)
        self.assertIn("v181_next_seen==1u&&v182_burst_seen==0u",V182_SC_FALLBACK)
        self.assertTrue(re.fullmatch(
            FALLBACK,"V182_SC_FALLBACK phase=1 prior=1 vector=1 flush=1 burst=3 "
                     "mapped=1 status=1 pc=805222e8 lr=80519904"))
        self.assertNotIn("ctx.mmu.write",V182_SC_FALLBACK)
        self.assertNotIn("ipc70_bus.write",V182_SC_FALLBACK)
        self.assertEqual(self.before.count("original cache flush did not reach authentic syscall"),
                         self.after.count("original cache flush did not reach authentic syscall"))

    def test_late_v112_failure_only_prints_bounded_phase_without_bypass(self):
        self.assertEqual(self.before.count(V112_SYSCALL_GUARD),1)
        self.assertEqual(self.after.count(V182_V112_TELEMETRY),1)
        self.assertEqual(self.after.count("V112 original IOS_OpenAsync native cache syscall differs"),
                         self.before.count("V112 original IOS_OpenAsync native cache syscall differs"))
        self.assertIn("v181_next_seen==1u&&v182_burst_seen==0u",V182_V112_TELEMETRY)
        self.assertIn('check(order&&count,"V112 original IOS_OpenAsync native cache syscall differs");',
                      V182_V112_TELEMETRY)
        self.assertTrue(re.fullmatch(
            DEP,"V182_V112_DEP phase=1 op=1 flush=1 sc=1 vector=1 order=0 "
                "count=0 calls=0 pc=805222e8 lr=80519904"))
        self.assertFalse(re.fullmatch(
            DEP,"V182_V112_DEP phase=1 op=1 flush=1 sc=1 vector=1 order=0 "
                "count=0 calls=9 pc=805222e8 lr=80519904"))
        self.assertNotIn("ctx.mmu.write",V182_V112_TELEMETRY)
        self.assertNotIn("ipc70_bus.write",V182_V112_TELEMETRY)

    def test_final_original_guest_endpoint_validates_prior_milestones(self):
        self.assertGreaterEqual(len(PAIR.findall(self.before)),7)
        self.assertEqual(len(PAIR.findall(self.after)),len(PAIR.findall(self.before)))
        for label in ("V178 original SC reply burst did not reach bounded native checkpoint",
                      "V180 original SC reply successor did not reach another native function",
                      "V181 original SC reply successor did not reach another native function"):
            end=self.after.index('"'+label+'");')
            start=self.after.rfind("check(",0,end)
            self.assertIn("v182_burst_seen==1u",self.after[start:end])
        with self.assertRaises(ValueError):derive("invalid")
        with self.assertRaises(ValueError):widen_prior("invalid")

    def test_sixteen_trials_and_private_cleanup(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        self.assertIn("derive_v182_sc_reply_burst_harness.py",script)
        self.assertIn("V181_SC_NEXT verified=1",script)
        self.assertIn("V182_SC_BURST verified=1",script)
        self.assertIn("V182_CACHE_SC verified=1",script)
        self.assertIn('trap \'rm -rf -- "$work"\' EXIT',script)
        good=("V182_SC_BURST calls=8 clean=1 reply=1 queue=1 guest=1 "
              "caller=1 coherent=1 mapped=1 before=1 status=1 changed=0 "
              "pc=8051ad38 lr=80519888")
        self.assertTrue(re.fullmatch(PASS,good))
        self.assertTrue(re.fullmatch(PASS,good.replace("calls=8","calls=3").replace("status=1 changed=0","status=0 changed=1")))
        self.assertFalse(re.fullmatch(PASS,good.replace("calls=8","calls=9")))
        self.assertTrue(re.fullmatch(TRACE,"V182_SC_TRACE step=8 pc=8051ad38 lr=80519888"))
        with tempfile.TemporaryDirectory() as td:
            output=Path(td)/"runner.sh"
            output.write_text(script,encoding="utf-8")
            subprocess.run(["bash","-n",str(output)],check=True)

    def test_public_assertion_labels_use_this_exact_derived_v182_catalog(self):
        from diagnose_v182_sc_reply_burst import describe
        from classify_v38_native_failure import STRING
        labels=sorted(set(STRING.findall(self.after)))
        target="V112 original IOS_OpenAsync native cache syscall differs"
        self.assertEqual(describe(labels.index(target)+1),target)
        with self.assertRaises(ValueError): describe(0)
        with self.assertRaises(ValueError): describe(10000)

    def test_original_private_job_is_separate(self):
        wf=(HERE.parents[1]/".github/workflows/wii-v182-sc-reply-burst.yml").read_text(encoding="utf-8")
        self.assertIn("run_v182_sc_reply_burst.sh",wf)
        self.assertIn("V182_SC_BURST verified=1",wf)
        self.assertIn("  cancel-in-progress: false",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)

if __name__=="__main__":
    unittest.main()
