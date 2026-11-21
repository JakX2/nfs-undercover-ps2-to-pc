#!/usr/bin/env python3
"""V190 original-free Wii second IOS ACK rescheduler guest execution tests."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v189_second_ios_restore_harness import derive as previous
from derive_v190_second_ios_resched_harness import derive,STOP,CONTINUE,OBSERVER,NEXT_TRIAL,PAIR,widen_prior
from derive_v190_second_ios_resched_runner import derive as runner,PATTERN,PASS,STATE,PASS_STATE
HERE=Path(__file__).resolve().parent
class V190(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        src=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=previous(src)
        cls.after=derive(src)

    def test_exact_authentic_wii_rescheduler_entry_executed(self):
        self.assertIn(STOP,self.before)
        self.assertNotIn(STOP,self.after)
        self.assertIn(CONTINUE,self.after)
        self.assertIn("addr==0x80529940u&&ctx.lr==0x80526cb4u",CONTINUE)
        self.assertIn("!ee&&!ready",CONTINUE)
        self.assertIn("return; // execute authentic original Wii rescheduler function",CONTINUE)
        self.assertIn("v189_next_seen==1u&&v186_ack_seen==1u&&v190_next_seen==0u",OBSERVER)
        self.assertIn("ctx.inst_count>v190_start_inst",OBSERVER)
        self.assertIn("V190_SC_NEXT y2=",OBSERVER)
        self.assertIn(NEXT_TRIAL,self.after)

    def test_queue_remains_intact_and_no_synthetic_ios_or_cpu_write(self):
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
        self.assertIn("ipc70_bus.external_exception_pending(ctx.msr)",OBSERVER)
        for marker in ("V189_SC_NEXT y2=","V189_SC_STATE guest=",
                       "V188_SC_NEXT y2=","V186_SECOND_ACK ack="):
            self.assertEqual(self.before.count(marker),self.after.count(marker),marker)

    def test_bounded_prior_original_guest_assertions(self):
        self.assertGreaterEqual(len(PAIR.findall(self.before)),7)
        self.assertEqual(len(PAIR.findall(self.before)),len(PAIR.findall(self.after)))
        for label in ("V171 original SC reply processor did not reach distinct native callee",
                      "V185 original IPC Y1 reader did not reach authentic native successor"):
            end=self.after.index('"'+label+'");')
            start=self.after.rfind("check(",0,end)
            self.assertIn("v190_next_seen==1u",self.after[start:end])
        for marker in ("const bool v186_guest=","const bool v187_guest=",
                       "const bool v188_guest=","const bool v189_guest="):
            begin=self.after.index(marker);end=self.after.index("const bool ",begin+len(marker))
            self.assertIn("v190_next_seen==1u",self.after[begin:end])
        with self.assertRaises(ValueError):derive("invalid")
        with self.assertRaises(ValueError):widen_prior("invalid")

    def test_owner_native_runner_and_workflow(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        self.assertIn("derive_v190_second_ios_resched_harness.py",script)
        self.assertIn("V189_SC_RESTORE verified=1",script)
        self.assertIn("V190_SC_RESCHED verified=1",script)
        good=("V190_SC_NEXT y2=1 flag=1 queue=1 request=1 guest=1 caller=1 "
              "coherent=1 mapped=1 sc=1 ee=0 ready=0 pc=805229b4 lr=80526cbc")
        self.assertTrue(re.fullmatch(PASS,good))
        self.assertFalse(re.fullmatch(PASS,good.replace("caller=1","caller=0")))
        self.assertTrue(re.fullmatch(PATTERN,good.replace("sc=1","sc=0")))
        self.assertTrue(re.fullmatch(STATE,PASS_STATE.strip("^$")))
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"script.sh";p.write_text(script,encoding="utf-8")
            subprocess.run(["bash","-n",str(p)],check=True)
        wf=(HERE.parents[1]/".github/workflows/wii-v190-second-ios-resched.yml").read_text()
        self.assertIn("run_v190_second_ios_resched.sh",wf)
        self.assertIn("V190_SC_RESCHED verified=1",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)

if __name__=="__main__":
    unittest.main()
