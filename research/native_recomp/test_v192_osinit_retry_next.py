#!/usr/bin/env python3
"""V192 source-only tests for authentic OSInit helper PPC continuation."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v191_second_ios_next_harness import derive as previous
from derive_v192_osinit_retry_next_harness import (
    derive,STOP,CONTINUE,OBSERVER,NEXT_TRIAL,PAIR,widen_prior,
)
from derive_v192_osinit_retry_next_runner import derive as runner,PASS,PATTERN,STATE,PASS_STATE
HERE=Path(__file__).resolve().parent

class V192(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=previous(source)
        cls.after=derive(source)

    def test_exact_original_osinit_helper_is_executed(self):
        self.assertIn(STOP,self.before)
        self.assertNotIn(STOP,self.after)
        self.assertIn(CONTINUE,self.after)
        self.assertIn("addr==0x8052f830u&&ctx.lr==0x80520970u",CONTINUE)
        self.assertIn("sc==1u&&ee&&ready",CONTINUE)
        self.assertIn("return; // execute actual original Wii OSInit retry helper",CONTINUE)
        self.assertIn("v191_next_seen==1u&&v186_ack_seen==1u&&v192_next_seen==0u",OBSERVER)
        self.assertIn("ctx.inst_count>v192_start_inst",OBSERVER)
        self.assertIn("addr==0x80000500u",OBSERVER)
        self.assertIn("V192_OSINIT_NEXT y2=",OBSERVER)
        self.assertIn(NEXT_TRIAL,self.after)

    def test_no_injected_ios_step_guest_memory_or_status_mutation(self):
        for token in ("ctx.mmu.write8(", "ctx.mmu.write16(", "ctx.mmu.write32(",
                      "ipc70_ram.write8(", "ipc70_bus.write32(",
                      "ipc70_bus.tick(", "scheduler.service_one(ctx.msr)"):
            self.assertEqual(self.before.count(token),self.after.count(token),token)
        for block in (CONTINUE,OBSERVER):
            for bad in ("ctx.mmu.write","ipc70_ram.write","ipc70_bus.write",
                        "scheduler.service_one(", "ipc70_bus.tick(", "ctx.msr="):
                self.assertNotIn(bad,block)
        self.assertIn("const bool retry=addr==0x8052f830u",OBSERVER)
        self.assertIn("const bool vector=addr==0x80000500u",OBSERVER)

    def test_prior_authentic_owner_proofs_retained(self):
        self.assertGreaterEqual(len(PAIR.findall(self.before)),7)
        self.assertEqual(len(PAIR.findall(self.before)),len(PAIR.findall(self.after)))
        for name in ("const bool v190_guest=","const bool v191_guest="):
            start=self.after.index(name)
            end=self.after.index("const bool ",start+len(name))
            self.assertIn("v192_next_seen==1u",self.after[start:end])
        with self.assertRaises(ValueError):derive("invalid")
        with self.assertRaises(ValueError):widen_prior("invalid")

    def test_owner_runner_is_bounded_and_shell_safe(self):
        original=(HERE/"run_v79_continuous_reply_entry.sh").read_text(encoding="utf-8")
        script=runner(original)
        self.assertIn("derive_v192_osinit_retry_next_harness.py",script)
        self.assertIn("V191_SC_NEXT verified=1",script)
        self.assertIn("V192_GUEST_PROBE next=$v192_next state=$v192_state",script)
        self.assertIn("V192_OSINIT_NEXT verified=1",script)
        self.assertIn("V191_SHELL_GUARD line=$LINENO code=$?",script)
        good=("V192_OSINIT_NEXT y2=1 flag=1 queue=1 guest=1 coherent=1 mapped=1 "
              "caller=1 retry=1 vector=0 sc=1 ee=1 ready=1 r3=1 eq=1 "
              "pc=8052f830 lr=80520970")
        self.assertTrue(re.fullmatch(PASS,good))
        self.assertFalse(re.fullmatch(PASS,good.replace("guest=1","guest=0")))
        self.assertTrue(re.fullmatch(PATTERN,good.replace("coherent=1","coherent=0")))
        self.assertTrue(re.fullmatch(STATE,PASS_STATE.strip("^$")))
        with tempfile.TemporaryDirectory() as root:
            f=Path(root)/"runner.sh";f.write_text(script,encoding="utf-8")
            subprocess.run(["bash","-n",str(f)],check=True)

    def test_owner_workflow_original_code_remains_private(self):
        wf=(HERE.parents[1]/".github/workflows/wii-v192-osinit-retry-next.yml").read_text()
        self.assertIn("run_v192_osinit_retry_next.sh",wf)
        self.assertIn("V192_OSINIT_NEXT verified=1",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)

if __name__=="__main__":
    unittest.main()
