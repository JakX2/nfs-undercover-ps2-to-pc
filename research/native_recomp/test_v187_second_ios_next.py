#!/usr/bin/env python3
"""V187 source-only regression for original Wii scheduler after second Y2 ACK."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v186_second_ios_ack_harness import derive as previous
from derive_v187_second_ios_next_harness import (
    derive, STOP, CONTINUE, OBSERVER, NEXT_TRIAL, PAIR,
    V186_GUEST, V187_GUEST, widen_prior,
)
from derive_v187_second_ios_next_runner import (
    derive as runner, PASS, PATTERN, PASS_STATE, STATE
)
HERE=Path(__file__).resolve().parent

class V187(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=previous(base)
        cls.after=derive(base)

    def test_execute_exact_authenticated_original_scheduler_after_y2_ack(self):
        self.assertIn(STOP,self.before)
        self.assertNotIn(STOP,self.after)
        self.assertIn(CONTINUE,self.after)
        self.assertIn("addr==0x80529434u&&ctx.lr==0x80526cb0u",CONTINUE)
        self.assertIn("v186_queued&&v186_consumed&&v186_request&&v186_cpu",CONTINUE)
        self.assertIn("v187_start_inst=ctx.inst_count",CONTINUE)
        self.assertIn("return; // continue original Wii guest scheduler",CONTINUE)
        self.assertIn("v186_ack_seen==1u&&v185_next_seen==1u&&v187_next_seen==0u",OBSERVER)
        self.assertIn("ctx.inst_count>v187_start_inst",OBSERVER)
        self.assertIn("V187_SC_NEXT y2=",OBSERVER)
        self.assertIn(NEXT_TRIAL,self.after)

    def test_original_hardware_state_without_ios_reply_fabrication(self):
        for token in ("ctx.mmu.write8(", "ctx.mmu.write16(", "ctx.mmu.write32(",
                      "ipc70_ram.write8(", "ipc70_bus.write32(",
                      "ipc70_bus.tick(", "scheduler.service_one(ctx.msr)"):
            self.assertEqual(self.before.count(token),self.after.count(token),token)
        for block in (CONTINUE,OBSERVER):
            for token in ("ctx.mmu.write", "ipc70_ram.write", "ipc70_bus.write32",
                          "scheduler.service_one(", "ipc70_bus.tick("):
                self.assertNotIn(token,block)
        self.assertIn("queued_replies()==1u",OBSERVER)
        self.assertIn("!ipc70_bus.pending_native_ios_request()",OBSERVER)
        self.assertIn("ipc70_ram.read32(v183_second_phys)==IOS::Open",OBSERVER)
        self.assertIn("Mail::Y2",OBSERVER)
        self.assertIn("Irq::IPC_PPC",OBSERVER)
        for label in ("V186_SECOND_ACK ack=","V186_ACK_STATE guest=",
                      "V185_SC_NEXT clean=","V183_SECOND_CTRL phase=1"):
            self.assertEqual(self.before.count(label),self.after.count(label),label)

    def test_only_scope_earlier_native_pc_lr_guards_after_v187_success(self):
        self.assertGreaterEqual(len(PAIR.findall(self.before)),7)
        self.assertEqual(len(PAIR.findall(self.before)),len(PAIR.findall(self.after)))
        self.assertIn(V186_GUEST,self.before)
        self.assertIn(V187_GUEST,self.after)
        for label in ("V171 original SC reply processor did not reach distinct native callee",
                      "V183 original SC reply IPC followup did not reach bounded guest call",
                      "V185 original IPC Y1 reader did not reach authentic native successor"):
            end=self.after.index('"'+label+'");')
            start=self.after.rfind("check(",0,end)
            self.assertIn("v187_next_seen==1u",self.after[start:end])
        with self.assertRaises(ValueError):derive("invalid")
        with self.assertRaises(ValueError):widen_prior("invalid")

    def test_owner_runner_sixteen_trials_and_bounds(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text(encoding="utf-8"))
        self.assertIn("derive_v187_second_ios_next_harness.py",script)
        self.assertIn("V186_SECOND_ACK verified=1",script)
        self.assertIn("V187_SC_NEXT verified=1",script)
        sample=("V187_SC_NEXT y2=1 flag=1 queue=1 request=1 guest=1 "
                "caller=1 coherent=1 mapped=1 sc=1 pc=805265ac lr=80529448")
        self.assertTrue(re.fullmatch(PASS,sample))
        self.assertTrue(re.fullmatch(PATTERN,sample.replace("guest=1","guest=0")))
        self.assertFalse(re.fullmatch(PASS,sample.replace("guest=1","guest=0")))
        self.assertTrue(re.fullmatch(STATE,PASS_STATE.strip("^$")))
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"runner.sh"
            path.write_text(script,encoding="utf-8")
            subprocess.run(["bash","-n",str(path)],check=True)

    def test_owner_workflow_preserves_private_cleanup(self):
        wf=(HERE.parents[1]/".github/workflows/wii-v187-second-ios-next.yml").read_text()
        self.assertIn("run_v187_second_ios_next.sh",wf)
        self.assertIn("V187_SC_NEXT verified=1",wf)
        self.assertIn("  cancel-in-progress: false",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)

if __name__=="__main__":
    unittest.main()
