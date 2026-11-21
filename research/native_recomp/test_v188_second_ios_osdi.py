#!/usr/bin/env python3
"""V188 source-only original Wii second IOS ACK interrupt-disable tests."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v187_second_ios_next_harness import derive as previous
from derive_v188_second_ios_osdi_harness import derive, STOP, CONTINUE, OBSERVER, NEXT_TRIAL, PAIR, widen_prior
from derive_v188_second_ios_osdi_runner import derive as runner, PASS, PATTERN, STATE, PASS_STATE
HERE=Path(__file__).resolve().parent
class V188(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=previous(base)
        cls.after=derive(base)

    def test_original_osdi_after_second_y2_ack_executes(self):
        self.assertIn(STOP,self.before)
        self.assertNotIn(STOP,self.after)
        self.assertIn(CONTINUE,self.after)
        self.assertIn("addr==0x805265acu&&ctx.lr==0x80529448u",CONTINUE)
        self.assertIn("v188_start_inst=ctx.inst_count",CONTINUE)
        self.assertIn("return; // execute original Wii interrupt-disable",CONTINUE)
        self.assertIn("v187_next_seen==1u&&v186_ack_seen==1u&&v188_next_seen==0u",OBSERVER)
        self.assertIn("ctx.inst_count>v188_start_inst",OBSERVER)
        self.assertIn("V188_SC_NEXT y2=",OBSERVER)
        self.assertIn(NEXT_TRIAL,self.after)

    def test_real_irq_remains_pending_with_no_synthetic_ios_or_cpu_state(self):
        for token in ("ctx.mmu.write8(", "ctx.mmu.write16(", "ctx.mmu.write32(",
                      "ipc70_ram.write8(", "ipc70_bus.write32(",
                      "ipc70_bus.tick(", "scheduler.service_one(ctx.msr)"):
            self.assertEqual(self.before.count(token),self.after.count(token),token)
        for block in (CONTINUE,OBSERVER):
            for token in ("ctx.mmu.write", "ipc70_ram.write", "ipc70_bus.write",
                          "scheduler.service_one(", "ipc70_bus.tick("):
                self.assertNotIn(token,block)
        self.assertIn("queued_replies()==1u",OBSERVER)
        self.assertIn("!ipc70_bus.pending_native_ios_request()",OBSERVER)
        self.assertIn("ipc70_ram.read32(v183_second_phys)==IOS::Open",OBSERVER)
        self.assertIn("(ctx.msr&Bus::MSR_EE)==0u",OBSERVER)
        self.assertIn("Irq::IPC_PPC",OBSERVER)
        for marker in ("V187_SC_NEXT y2=","V187_SC_STATE guest=",
                       "V186_SECOND_ACK ack=","V185_IPC_ENTRY phase=1"):
            self.assertEqual(self.before.count(marker),self.after.count(marker),marker)

    def test_strict_prior_guest_assertions_continue_to_new_observed_function(self):
        self.assertGreaterEqual(len(PAIR.findall(self.before)),7)
        self.assertEqual(len(PAIR.findall(self.before)),len(PAIR.findall(self.after)))
        for label in ("V171 original SC reply processor did not reach distinct native callee",
                      "V185 original IPC Y1 reader did not reach authentic native successor"):
            end=self.after.index('"'+label+'");')
            start=self.after.rfind("check(",0,end)
            self.assertIn("v188_next_seen==1u",self.after[start:end])
        with self.assertRaises(ValueError):derive("invalid")
        with self.assertRaises(ValueError):widen_prior("invalid")

    def test_v186_and_v187_derived_guest_predicates_accept_authentic_v188_stop(self):
        for begin,end in (
            ("const bool v186_guest=","const bool v186_mail="),
            ("const bool v187_guest=","const bool v187_queue="),
        ):
            first=self.after.index(begin);last=self.after.index(end,first)
            self.assertIn("v188_next_seen==1u",self.after[first:last])
            self.assertIn("c.pc==nwii::runtime::v188_target_pc",self.after[first:last])
        self.assertEqual(self.before.count("V186_ACK_STATE guest="),
                         self.after.count("V186_ACK_STATE guest="))
        self.assertEqual(self.before.count("V187_SC_STATE guest="),
                         self.after.count("V187_SC_STATE guest="))

    def test_private_owner_runner_checks_sixteen_and_bash(self):
        s=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        self.assertIn("derive_v188_second_ios_osdi_harness.py",s)
        self.assertIn("V187_SC_NEXT verified=1",s)
        self.assertIn("V188_SC_OSDI verified=1",s)
        sample=("V188_SC_NEXT y2=1 flag=1 queue=1 request=1 guest=1 caller=1 "
                "masked=1 coherent=1 mapped=1 sc=1 pc=805265d4 lr=80529468")
        self.assertTrue(re.fullmatch(PASS,sample))
        self.assertTrue(re.fullmatch(PATTERN,sample.replace("masked=1","masked=0")))
        self.assertFalse(re.fullmatch(PASS,sample.replace("masked=1","masked=0")))
        self.assertTrue(re.fullmatch(STATE,PASS_STATE.strip("^$")))
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"runner.sh"
            p.write_text(s,encoding="utf-8")
            subprocess.run(["bash","-n",str(p)],check=True)

    def test_workflow_safeguards(self):
        wf=(HERE.parents[1]/".github/workflows/wii-v188-second-ios-osdi.yml").read_text()
        self.assertIn("run_v188_second_ios_osdi.sh",wf)
        self.assertIn("V188_SC_OSDI verified=1",wf)
        self.assertIn("  cancel-in-progress: false",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)

if __name__=="__main__":
    unittest.main()
