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
    PREVIOUS_FOLLOWUP, widen_prior,
)
from derive_v182_sc_reply_burst_runner import derive as runner, PASS, TRACE

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

    def test_final_original_guest_endpoint_validates_prior_milestones(self):
        self.assertGreaterEqual(len(PAIR.findall(self.before)),7)
        self.assertEqual(len(PAIR.findall(self.after)),len(PAIR.findall(self.before)))
        for label in ("V178 original SC reply burst did not reach bounded native checkpoint",
                      "V180 original SC reply successor did not reach another native function",
                      "V181 original second allocator call did not reach next native guest function"):
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

    def test_original_private_job_is_separate(self):
        wf=(HERE.parents[1]/".github/workflows/wii-v182-sc-reply-burst.yml").read_text(encoding="utf-8")
        self.assertIn("run_v182_sc_reply_burst.sh",wf)
        self.assertIn("V182_SC_BURST verified=1",wf)
        self.assertIn("  cancel-in-progress: false",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)

if __name__=="__main__":
    unittest.main()
