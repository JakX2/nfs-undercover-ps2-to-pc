#!/usr/bin/env python3
"""V193 source-only checks for authentic Wii interrupt-disable continuation."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v192_osinit_retry_next_harness import derive as previous
from derive_v193_osdi_next_harness import (
    derive,STOP,CONTINUE,OBSERVER,NEXT_TRIAL,PAIR,widen_prior,
)
from derive_v193_osdi_next_runner import derive as runner,PASS,PATTERN,STATE,PASS_STATE
HERE=Path(__file__).resolve().parent

class V193(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=previous(base)
        cls.after=derive(base)

    def test_authenticated_original_interrupt_disable_is_executed(self):
        self.assertIn(STOP,self.before)
        self.assertNotIn(STOP,self.after)
        self.assertIn(CONTINUE,self.after)
        self.assertIn("addr==0x805265acu&&ctx.lr==0x8052f84cu",CONTINUE)
        self.assertIn("sc==1u&&ee&&ready",CONTINUE)
        self.assertIn("return; // execute original Wii OSDisableInterrupts helper",CONTINUE)
        self.assertIn("v192_next_seen==1u&&v191_next_seen==1u&&v193_next_seen==0u",OBSERVER)
        self.assertIn("ctx.inst_count>v193_start_inst",OBSERVER)
        self.assertIn("V193_OSDI_NEXT y2=",OBSERVER)
        self.assertIn(NEXT_TRIAL,self.after)

    def test_no_synthetic_interrupt_ios_reply_or_guest_state_write(self):
        for token in ("ctx.mmu.write8(", "ctx.mmu.write16(", "ctx.mmu.write32(",
                      "ipc70_ram.write8(", "ipc70_bus.write32(",
                      "ipc70_bus.tick(", "scheduler.service_one(ctx.msr)"):
            self.assertEqual(self.before.count(token),self.after.count(token),token)
        for block in (CONTINUE,OBSERVER):
            for forbidden in ("ctx.mmu.write","ipc70_ram.write","ipc70_bus.write",
                              "scheduler.service_one(", "ipc70_bus.tick(", "ctx.msr="):
                self.assertNotIn(forbidden,block)

    def test_previous_guest_proofs_survive_original_continuation(self):
        self.assertGreaterEqual(len(PAIR.findall(self.before)),7)
        self.assertEqual(len(PAIR.findall(self.before)),len(PAIR.findall(self.after)))
        for name in ("const bool v191_guest=","const bool v192_guest="):
            a=self.after.index(name);b=self.after.index("const bool ",a+len(name))
            self.assertIn("v193_next_seen==1u",self.after[a:b])
        with self.assertRaises(ValueError):derive("invalid")
        with self.assertRaises(ValueError):widen_prior("invalid")

    def test_owner_runner_is_bounded_and_bash_valid(self):
        source=(HERE/"run_v79_continuous_reply_entry.sh").read_text(encoding="utf-8")
        script=runner(source)
        self.assertIn("derive_v193_osdi_next_harness.py",script)
        self.assertIn("V192_OSINIT_NEXT verified=1",script)
        self.assertIn("V193_GUEST_PROBE next=$v193_next state=$v193_state",script)
        self.assertIn("V193_OSDI_NEXT verified=1",script)
        self.assertIn("V153_SC_REPLY_STATE bridge=1 wire=1 mail=0 drained=0 irq=1",script)
        self.assertNotIn("grep -Fx 'V153_SC_REPLY_STATE bridge=1 wire=1 mail=0 drained=0 irq=0'",script)
        good=("V193_OSDI_NEXT y2=1 flag=1 queue=1 guest=1 coherent=1 mapped=1 "
              "caller=1 sc=1 ee=0 ready=0 r3=1 eq=1 pc=805265d4 lr=8052f850")
        self.assertTrue(re.fullmatch(PASS,good))
        self.assertFalse(re.fullmatch(PASS,good.replace("guest=1","guest=0")))
        self.assertTrue(re.fullmatch(PATTERN,good.replace("coherent=1","coherent=0")))
        self.assertTrue(re.fullmatch(STATE,PASS_STATE.strip("^$")))
        with tempfile.TemporaryDirectory() as root:
            f=Path(root)/"runner.sh";f.write_text(script,encoding="utf-8")
            subprocess.run(["bash","-n",str(f)],check=True)

    def test_private_workflow_cleanup_and_no_uploaded_owner_artifacts(self):
        wf=(HERE.parents[1]/".github/workflows/wii-v193-osdi-next.yml").read_text()
        self.assertIn("run_v193_osdi_next.sh",wf)
        self.assertIn("V193_OSDI_NEXT verified=1",wf)
        self.assertIn("V153_SC_REPLY_STATE bridge=1 wire=1 mail=0 drained=0 irq=1",wf)
        self.assertNotIn("V153_SC_REPLY_STATE bridge=1 wire=1 mail=0 drained=0 irq=0",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)

if __name__=="__main__":
    unittest.main()
