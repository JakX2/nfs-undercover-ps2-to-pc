#!/usr/bin/env python3
"""V191 original-free next Wii PPC guest call after second native IOS reschedule."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v190_second_ios_resched_harness import derive as previous
from derive_v191_second_ios_next_harness import (
    derive, STOP, CONTINUE, OBSERVER, NEXT_TRIAL, PAIR, widen_prior,
)
from derive_v191_second_ios_next_runner import derive as runner, PATTERN, PASS, STATE, PASS_STATE
HERE=Path(__file__).resolve().parent

class V191(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=previous(base)
        cls.after=derive(base)

    def test_exact_verified_guest_frontier_executes_original_function(self):
        self.assertIn(STOP,self.before)
        self.assertNotIn(STOP,self.after)
        self.assertIn(CONTINUE,self.after)
        self.assertIn("addr==0x805229b4u&&ctx.lr==0x80526cbcu",CONTINUE)
        self.assertIn("queue&&request&&guest&&caller&&coherent&&mapped&&sc",CONTINUE)
        self.assertIn("!ee&&!ready",CONTINUE)
        self.assertIn("return; // execute original Wii PPC context helper",CONTINUE)
        self.assertIn("v190_next_seen==1u&&v186_ack_seen==1u&&v191_next_seen==0u",OBSERVER)
        self.assertIn("ctx.inst_count>v191_start_inst",OBSERVER)
        self.assertIn("V191_SC_NEXT y2=",OBSERVER)
        self.assertIn(NEXT_TRIAL,self.after)

    def test_ipc_and_cpu_remain_unmodified_by_new_observer(self):
        for token in ("ctx.mmu.write8(", "ctx.mmu.write16(", "ctx.mmu.write32(",
                      "ipc70_ram.write8(", "ipc70_bus.write32(",
                      "ipc70_bus.tick(", "scheduler.service_one(ctx.msr)"):
            self.assertEqual(self.before.count(token),self.after.count(token),token)
        for part in (CONTINUE,OBSERVER):
            for forbidden in ("ctx.mmu.write","ipc70_ram.write","ipc70_bus.write",
                              "scheduler.service_one(", "ipc70_bus.tick(", "ctx.msr="):
                self.assertNotIn(forbidden,part)
        self.assertIn("queued_replies()==1u",OBSERVER)
        self.assertIn("ipc70_ram.read32(v183_second_phys)==IOS::Open",OBSERVER)

    def test_all_inherited_guest_predicates_accept_later_verified_endpoint(self):
        self.assertGreaterEqual(len(PAIR.findall(self.before)),7)
        self.assertEqual(len(PAIR.findall(self.before)),len(PAIR.findall(self.after)))
        for label in ("V171 original SC reply processor did not reach distinct native callee",
                      "V185 original IPC Y1 reader did not reach authentic native successor"):
            e=self.after.index('"'+label+'");')
            a=self.after.rfind("check(",0,e)
            self.assertIn("v191_next_seen==1u",self.after[a:e])
        self.assertIn("V190 original Wii rescheduler did not retain second IOS IPC state",self.after)
        with self.assertRaises(ValueError):derive("invalid")
        with self.assertRaises(ValueError):widen_prior("invalid")

    def test_sixteen_owner_trials_and_safe_script(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        self.assertIn("derive_v191_second_ios_next_harness.py",script)
        self.assertIn("V190_SC_RESCHED verified=1",script)
        self.assertIn("V191_SC_NEXT verified=1",script)
        self.assertIn('trap \'rm -rf -- "$work"\' EXIT',script)
        good=("V191_SC_NEXT y2=1 flag=1 queue=1 request=1 guest=1 caller=1 "
              "coherent=1 mapped=1 sc=1 ee=0 ready=0 pc=805229b4 lr=80526cbc")
        self.assertTrue(re.fullmatch(PASS,good))
        self.assertTrue(re.fullmatch(STATE,PASS_STATE.strip("^$")))
        self.assertFalse(re.fullmatch(PASS,good.replace("guest=1","guest=0")))
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/"run.sh";f.write_text(script)
            subprocess.run(["bash","-n",str(f)],check=True)

    def test_private_owner_workflow_cleanup(self):
        wf=(HERE.parents[1]/".github/workflows/wii-v191-second-ios-next.yml").read_text()
        self.assertIn("run_v191_second_ios_next.sh",wf)
        self.assertIn("V191_SC_NEXT verified=1",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)

if __name__=="__main__":
    unittest.main()
