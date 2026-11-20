#!/usr/bin/env python3
"""Original-free V179 SYSCONF reply continuation harness regression gates."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v178_sc_reply_burst_harness import derive as previous
from derive_v179_sc_reply_next_harness import (
    derive, STATE, RESET, STOP, CONTINUE, PREVIOUS_OBSERVER, OBSERVER_HEADER,
    FOLLOWUP, PREVIOUS_TRIAL, NEXT_TRIAL, PAIR, widen_prior,
)
from derive_v179_sc_reply_next_runner import derive as runner, PASS, PATTERN

HERE=Path(__file__).resolve().parent

class V179(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=previous(cls.base)
        cls.after=derive(cls.base)

    def test_verified_guest_callee_is_resumed_without_rewriting_game_state(self):
        self.assertIn(STOP,self.before)
        self.assertNotIn(STOP,self.after)
        self.assertIn(CONTINUE,self.after)
        self.assertIn("addr==0x8051982cu&&ctx.lr==0x804f1eccu",CONTINUE)
        self.assertIn("v178_calls==6u",CONTINUE)
        self.assertIn("status==1u&&!changed",CONTINUE)
        self.assertIn("return; // execute the authentic 0x8051982C",CONTINUE)
        self.assertEqual(PREVIOUS_OBSERVER.count(OBSERVER_HEADER),1)
        self.assertIn(FOLLOWUP,self.after)
        self.assertIn(NEXT_TRIAL,self.after)
        self.assertIn("ctx.inst_count>v179_start_inst",FOLLOWUP)
        self.assertIn("ctx.gpr[13]==v147_first_r13",FOLLOWUP)
        self.assertIn("const bool changed=mapped&&status!=v179_status_before",FOLLOWUP)

    def test_preserve_earlier_owner_proofs_and_original_ios_processing(self):
        for token in ("V177_SC_REPLY_NEXT clean=", "V178_SC_BURST calls=",
                      "V178_SC_TRACE step=", "unexpected original IPC submission dependency",
                      "unexpected original IPC client native dependency",
                      "unexpected original IPC ACK-only path dependency"):
            self.assertEqual(self.before.count(token),self.after.count(token),token)
        for token in ("ctx.mmu.write8(", "ctx.mmu.write16(", "ctx.mmu.write32(",
                      "ipc70_ram.write8(", "ipc70_bus.write32(",
                      "scheduler.service_one(ctx.msr)", "ipc70_bus.tick("):
            self.assertEqual(self.before.count(token),self.after.count(token),token)
        for token in ("v179_target_pc","v179_target_lr","v179_next_seen"):
            self.assertIn(token,self.after)

    def test_fail_closed_missing_guest_anchors_and_widen_earlier_checkpoints(self):
        self.assertGreaterEqual(len(PAIR.findall(self.before)),7)
        self.assertEqual(len(PAIR.findall(self.after)),len(PAIR.findall(self.before)))
        with self.assertRaises(ValueError):
            derive("invalid")
        with self.assertRaises(ValueError):
            widen_prior("invalid")
        for marker in (
            "V166 second SC reply nested interrupt restore did not reach real guest call",
            "V177 original SC reply handler callee did not enter subsequent native function",
            "V178 original SC reply burst did not reach bounded native checkpoint",
        ):
            end=self.after.index('"'+marker+'");')
            start=self.after.rfind("check(",0,end)
            self.assertIn("v179_next_seen==1u",self.after[start:end])

    def test_runner_privacy_and_sixteen_trials(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text(encoding="utf-8"))
        self.assertIn("derive_v179_sc_reply_next_harness.py",script)
        self.assertIn("V178_SC_BURST verified=1",script)
        self.assertIn("V179_SC_NEXT verified=1",script)
        self.assertIn('trap \'rm -rf -- "$work"\' EXIT',script)
        self.assertIn('test "$(grep -Ec',script)
        good=("V179_SC_NEXT clean=1 reply=1 queue=1 guest=1 "
              "caller=1 coherent=1 mapped=1 before=1 status=1 "
              "changed=0 pc=80519880 lr=80519840")
        self.assertTrue(re.fullmatch(PASS,good))
        self.assertTrue(re.fullmatch(PATTERN,good.replace("clean=1","clean=0")))
        self.assertFalse(re.fullmatch(PASS,good.replace("guest=1","guest=0")))
        with tempfile.TemporaryDirectory() as root:
            run=Path(root)/"runner.sh"
            run.write_text(script,encoding="utf-8")
            subprocess.run(["bash","-n",str(run)],check=True)

    def test_workflow_staging_and_private_cleaning(self):
        wf=(HERE.parents[1]/".github/workflows/wii-v179-sc-reply-next.yml").read_text(encoding="utf-8")
        self.assertIn("run_v179_sc_reply_next.sh",wf)
        self.assertIn("V179_SC_NEXT verified=1",wf)
        self.assertIn("  cancel-in-progress: false",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)

if __name__=="__main__":
    unittest.main()
