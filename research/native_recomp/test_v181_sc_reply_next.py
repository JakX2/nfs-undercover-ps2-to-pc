#!/usr/bin/env python3
"""V181 original-free SC reply helper continuation regression gates."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v180_sc_reply_next_harness import derive as previous
from derive_v181_sc_reply_next_harness import (
    derive, STOP, CONTINUE, FOLLOWUP, NEXT_TRIAL, PAIR, widen_prior,
)
from derive_v181_sc_reply_next_runner import derive as runner, PASS, PATTERN

HERE=Path(__file__).resolve().parent

class V181(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=previous(base)
        cls.after=derive(base)

    def test_enter_second_authentic_allocator_helper(self):
        self.assertIn(STOP,self.before)
        self.assertNotIn(STOP,self.after)
        self.assertIn(CONTINUE,self.after)
        self.assertIn("addr==0x8051ad38u&&ctx.lr==0x80519874u",CONTINUE)
        self.assertIn("v180_status_before==1u&&status==1u&&!changed",CONTINUE)
        self.assertIn("return; // execute authentic second 0x8051AD38",CONTINUE)
        self.assertIn("v180_next_seen==1u&&v181_next_seen==0u",FOLLOWUP)
        self.assertIn("ctx.inst_count>v181_start_inst",FOLLOWUP)
        self.assertIn("ctx.gpr[13]==v147_first_r13",FOLLOWUP)
        self.assertIn(NEXT_TRIAL,self.after)

    def test_source_only_does_not_mutate_guest_or_forge_service(self):
        for token in ("ctx.mmu.write8(", "ctx.mmu.write16(", "ctx.mmu.write32(",
                      "ipc70_ram.write8(", "ipc70_bus.write32(",
                      "scheduler.service_one(ctx.msr)", "ipc70_bus.tick("):
            self.assertEqual(self.before.count(token),self.after.count(token),token)
        self.assertNotIn("ctx.mmu.write",FOLLOWUP)
        self.assertNotIn("ipc70_bus.write",FOLLOWUP)
        for label in ("V179_SC_NEXT clean=", "V180_SC_NEXT clean=",
                      "V178_SC_BURST calls=", "unexpected original IPC client native dependency",
                      "native IOS_Open allocator tail entry differs"):
            self.assertEqual(self.before.count(label),self.after.count(label),label)

    def test_prior_pc_lr_proofs_preserved_and_fail_closed(self):
        self.assertGreaterEqual(len(PAIR.findall(self.before)),7)
        self.assertEqual(len(PAIR.findall(self.after)),len(PAIR.findall(self.before)))
        for label in ("V178 original SC reply burst did not reach bounded native checkpoint",
                      "V179 original SC reply continuation did not enter next PPC callee",
                      "V180 original SC reply successor did not reach another native function"):
            ending=self.after.index('"'+label+'");')
            start=self.after.rfind("check(",0,ending)
            self.assertIn("v181_next_seen==1u",self.after[start:ending])
        with self.assertRaises(ValueError): derive("invalid")
        with self.assertRaises(ValueError): widen_prior("invalid")

    def test_sixteen_trial_owner_runner_and_cleaning(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        self.assertIn("derive_v181_sc_reply_next_harness.py",script)
        self.assertIn("V180_SC_NEXT verified=1",script)
        self.assertIn("V181_SC_NEXT verified=1",script)
        self.assertIn('trap \'rm -rf -- "$work"\' EXIT',script)
        good=("V181_SC_NEXT clean=1 reply=1 queue=1 guest=1 caller=1 coherent=1 "
              "mapped=1 before=1 status=1 changed=0 pc=8051ab34 lr=8051ad64")
        self.assertTrue(re.fullmatch(PASS,good))
        self.assertFalse(re.fullmatch(PASS,good.replace("guest=1","guest=0")))
        self.assertTrue(re.fullmatch(PATTERN,good.replace("clean=1","clean=0")))
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"generated_runner.sh"
            path.write_text(script,encoding="utf-8")
            subprocess.run(["bash","-n",str(path)],check=True)

    def test_workflow_private_source_is_cleaned(self):
        wf=(HERE.parents[1]/".github/workflows/wii-v181-sc-reply-next.yml").read_text(encoding="utf-8")
        self.assertIn("run_v181_sc_reply_next.sh",wf)
        self.assertIn("V181_SC_NEXT verified=1",wf)
        self.assertIn("  cancel-in-progress: false",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)

if __name__=="__main__":
    unittest.main()
