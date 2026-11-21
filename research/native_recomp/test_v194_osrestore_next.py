#!/usr/bin/env python3
"""V194 original-free Wii PowerPC interrupt restore continuation checks."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v193_osdi_next_harness import derive as previous
from derive_v194_osrestore_next_harness import (
    derive,STOP,CONTINUE,OBSERVER,NEXT_TRIAL,PAIR,widen_prior,
)
from derive_v194_osrestore_next_runner import (
    derive as runner,PASS,PATTERN,STATE,PASS_STATE,
)
HERE=Path(__file__).resolve().parent

class V194(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=previous(base)
        cls.after=derive(base)

    def test_exact_v193_owner_verified_osrestore_helper_resumes(self):
        self.assertIn(STOP,self.before)
        self.assertNotIn(STOP,self.after)
        self.assertIn(CONTINUE,self.after)
        self.assertIn("addr==0x805265d4u&&ctx.lr==0x8052f92cu",CONTINUE)
        self.assertIn("sc==1u&&!ee&&!ready",CONTINUE)
        self.assertIn("return; // execute original Wii OSRestoreInterrupts",CONTINUE)
        self.assertIn("v193_next_seen==1u&&v192_next_seen==1u&&v194_next_seen==0u",OBSERVER)
        self.assertIn("ctx.inst_count>v194_start_inst",OBSERVER)
        self.assertIn("V194_RESTORE_NEXT y2=",OBSERVER)
        self.assertIn(NEXT_TRIAL,self.after)

    def test_owners_irq_and_cpu_state_are_not_fabricated(self):
        for token in ("ctx.mmu.write8(", "ctx.mmu.write16(", "ctx.mmu.write32(",
                      "ipc70_ram.write8(", "ipc70_bus.write32(",
                      "ipc70_bus.tick(", "scheduler.service_one(ctx.msr)"):
            self.assertEqual(self.before.count(token),self.after.count(token),token)
        for block in (CONTINUE,OBSERVER):
            for forbidden in ("ctx.mmu.write","ipc70_ram.write","ipc70_bus.write",
                              "scheduler.service_one(", "ipc70_bus.tick(", "ctx.msr="):
                self.assertNotIn(forbidden,block)
        self.assertIn("const bool coherent=ready==(ee&&ipc70_bus.external_irq_level())",OBSERVER)
        self.assertIn("check(y2&&flagset&&queue&&request&&guest&&coherent&&",OBSERVER)

    def test_prior_powerpc_guest_proofs_retained(self):
        self.assertGreaterEqual(len(PAIR.findall(self.before)),7)
        self.assertEqual(len(PAIR.findall(self.before)),len(PAIR.findall(self.after)))
        for predicate in ("const bool v192_guest=","const bool v193_guest="):
            a=self.after.index(predicate);b=self.after.index("const bool ",a+len(predicate))
            self.assertIn("v194_next_seen==1u",self.after[a:b])
        with self.assertRaises(ValueError):derive("invalid")
        with self.assertRaises(ValueError):widen_prior("invalid")

    def test_runner_phase_specific_v153_irq_and_native_gate(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        self.assertIn("derive_v194_osrestore_next_harness.py",script)
        self.assertIn("V194_GUEST_PROBE next=$v194_next state=$v194_state",script)
        self.assertIn("V194_RESTORE_NEXT verified=1",script)
        self.assertIn("grep -E '^V153_SC_REPLY_STATE bridge=1 wire=1 mail=0 drained=0 irq=[01]$'",script)
        self.assertNotIn("grep -Fx 'V153_SC_REPLY_STATE bridge=1 wire=1 mail=0 drained=0 irq=1'",script)
        good=("V194_RESTORE_NEXT y2=1 flag=1 queue=1 request=1 guest=1 coherent=1 "
              "mapped=1 caller=1 sc=1 ee=1 ready=1 vector=0 r3=1 eq=0 "
              "pc=8052f830 lr=80520970")
        self.assertTrue(re.fullmatch(PASS,good))
        self.assertFalse(re.fullmatch(PASS,good.replace("guest=1","guest=0")))
        self.assertTrue(re.fullmatch(PATTERN,good.replace("flag=1","flag=0")))
        self.assertTrue(re.fullmatch(STATE,PASS_STATE.strip("^$")))
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"run.sh";p.write_text(script,encoding="utf-8")
            subprocess.run(["bash","-n",str(p)],check=True)

    def test_private_owner_workflow_is_cleanup_safe(self):
        wf=(HERE.parents[1]/".github/workflows/wii-v194-osrestore-next.yml").read_text()
        self.assertIn("run_v194_osrestore_next.sh",wf)
        self.assertIn("V194_RESTORE_NEXT verified=1",wf)
        self.assertIn("V153_SC_REPLY_STATE bridge=1 wire=1 mail=0 drained=0 irq=[01]",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)

if __name__=="__main__":
    unittest.main()
