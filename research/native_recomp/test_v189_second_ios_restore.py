#!/usr/bin/env python3
"""V189 source-only original Wii second IOS ACK MSR interrupt restore checks."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v188_second_ios_osdi_harness import derive as previous
from derive_v189_second_ios_restore_harness import (
    derive, STOP, CONTINUE, OBSERVER, NEXT_TRIAL,
    PAIR, OLD_V188_CHECK, V189_SCOPED_CHECK, widen_prior,
)
from derive_v189_second_ios_restore_runner import (
    derive as runner, PATTERN, PASS, STATE, PASS_STATE
)
HERE=Path(__file__).resolve().parent
class V189(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=previous(base)
        cls.after=derive(base)

    def test_authentic_wii_restore_helper_executed_from_v188(self):
        self.assertIn(STOP,self.before)
        self.assertNotIn(STOP,self.after)
        self.assertIn(CONTINUE,self.after)
        self.assertIn("addr==0x805265d4u&&ctx.lr==0x80529458u",CONTINUE)
        self.assertIn("v189_start_inst=ctx.inst_count",CONTINUE)
        self.assertIn("return; // execute original Wii interrupt-restore",CONTINUE)
        self.assertIn("v188_next_seen==1u&&v186_ack_seen==1u&&v189_next_seen==0u",OBSERVER)
        self.assertIn("ctx.inst_count>v189_start_inst",OBSERVER)
        self.assertIn("V189_SC_NEXT y2=",OBSERVER)
        self.assertIn(NEXT_TRIAL,self.after)

    def test_no_fake_ios_service_msr_mutation_or_synthetic_reply(self):
        for token in ("ctx.mmu.write8(", "ctx.mmu.write16(", "ctx.mmu.write32(",
                      "ipc70_ram.write8(", "ipc70_bus.write32(",
                      "ipc70_bus.tick(", "scheduler.service_one(ctx.msr)"):
            self.assertEqual(self.before.count(token),self.after.count(token),token)
        for block in (CONTINUE,OBSERVER):
            for token in ("ctx.mmu.write", "ipc70_ram.write", "ipc70_bus.write",
                          "scheduler.service_one(", "ipc70_bus.tick(", "ctx.msr="):
                self.assertNotIn(token,block)
        self.assertIn("queued_replies()==1u",OBSERVER)
        self.assertIn("!ipc70_bus.pending_native_ios_request()",OBSERVER)
        self.assertIn("ipc70_ram.read32(v183_second_phys)==IOS::Open",OBSERVER)
        self.assertIn("const bool ee=(ctx.msr&Bus::MSR_EE)!=0u",OBSERVER)
        self.assertIn("const bool ready=ipc70_bus.external_exception_pending(ctx.msr)",OBSERVER)
        self.assertIn("V189_SC_NEXT y2=",OBSERVER)

    def test_first_masked_proof_stays_strict_then_records_actual_restored_ee(self):
        self.assertEqual(self.before.count(OLD_V188_CHECK),1)
        self.assertEqual(self.after.count(V189_SCOPED_CHECK),1)
        self.assertIn("v188_masked||nwii::runtime::v189_next_seen==1u",V189_SCOPED_CHECK)
        self.assertIn("const bool v188_masked=(c.msr&V188Bus::MSR_EE)==0u",self.after)
        for name in ("const bool v186_guest=","const bool v187_guest=","const bool v188_guest="):
            start=self.after.index(name)
            end=self.after.index("const bool ",start+len(name))
            self.assertIn("v189_next_seen==1u",self.after[start:end])

    def test_prior_original_guest_proofs_keep_bounded_authentic_endpoint(self):
        self.assertGreaterEqual(len(PAIR.findall(self.before)),7)
        self.assertEqual(len(PAIR.findall(self.before)),len(PAIR.findall(self.after)))
        for label in ("V171 original SC reply processor did not reach distinct native callee",
                      "V182 original SC reply call burst did not reach authenticated native stop",
                      "V185 original IPC Y1 reader did not reach authentic native successor"):
            end=self.after.index('"'+label+'");')
            start=self.after.rfind("check(",0,end)
            self.assertIn("v189_next_seen==1u",self.after[start:end])
        with self.assertRaises(ValueError):derive("invalid")
        with self.assertRaises(ValueError):widen_prior("invalid")

    def test_private_sixteen_trial_runner_safe_shell_syntax(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        self.assertIn("derive_v189_second_ios_restore_harness.py",script)
        self.assertIn("V188_SC_OSDI verified=1",script)
        self.assertIn("V189_SC_RESTORE verified=1",script)
        self.assertIn("masked=[01] sc=1",script)
        good=("V189_SC_NEXT y2=1 flag=1 queue=1 request=1 guest=1 caller=1 "
              "coherent=1 mapped=1 sc=1 ee=1 ready=1 pc=80519abc lr=8052947c")
        self.assertTrue(re.fullmatch(PASS,good))
        self.assertFalse(re.fullmatch(PASS,good.replace("coherent=1","coherent=0")))
        self.assertTrue(re.fullmatch(PATTERN,good.replace("guest=1","guest=0")))
        self.assertTrue(re.fullmatch(STATE,PASS_STATE.strip("^$").replace("ee=[01]","ee=1").replace("ready=[01]","ready=1")))
        with tempfile.TemporaryDirectory() as root:
            file=Path(root)/"script.sh";file.write_text(script,encoding="utf-8")
            subprocess.run(["bash","-n",str(file)],check=True)

    def test_privacy_owner_ci(self):
        wf=(HERE.parents[1]/".github/workflows/wii-v189-second-ios-restore.yml").read_text()
        self.assertIn("run_v189_second_ios_restore.sh",wf)
        self.assertIn("V189_SC_RESTORE verified=1",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertIn("  cancel-in-progress: false",wf)
        self.assertNotIn("upload-artifact",wf)

if __name__=="__main__":
    unittest.main()
