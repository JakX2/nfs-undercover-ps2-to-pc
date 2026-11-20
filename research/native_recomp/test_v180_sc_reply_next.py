#!/usr/bin/env python3
"""V180 owner-free native reply successor harness, safety and CI regressions."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v179_sc_reply_next_harness import derive as previous
from derive_v180_sc_reply_next_harness import (
    derive, STATE, RESET, STOP, CONTINUE, PREVIOUS_FOLLOWUP,
    FOLLOWUP, NEXT_TRIAL, PAIR, widen_prior,
)
from derive_v180_sc_reply_next_runner import derive as runner, PASS, PATTERN

HERE=Path(__file__).resolve().parent

class V180(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=previous(base)
        cls.after=derive(base)

    def test_execute_exact_owner_verified_v179_guest_function(self):
        self.assertIn(STOP,self.before)
        self.assertNotIn(STOP,self.after)
        self.assertIn(CONTINUE,self.after)
        self.assertIn("addr==0x80545104u&&ctx.lr==0x80519840u",CONTINUE)
        self.assertIn("v179_status_before==1u&&status==1u&&!changed",CONTINUE)
        self.assertIn("return; // execute genuine 0x80545104",CONTINUE)
        self.assertIn("v179_next_seen==1u&&v180_next_seen==0u",FOLLOWUP)
        self.assertIn("ctx.inst_count>v180_start_inst",FOLLOWUP)
        self.assertIn("ctx.gpr[13]==v147_first_r13",FOLLOWUP)
        self.assertIn(NEXT_TRIAL,self.after)

    def test_no_game_state_or_ios_injection(self):
        for label in ("V177_SC_REPLY_NEXT clean=", "V178_SC_BURST calls=",
                      "V179_SC_NEXT clean=", "V178_SC_TRACE step=",
                      "unexpected original IPC submission dependency",
                      "unexpected original IPC client native dependency"):
            self.assertEqual(self.before.count(label),self.after.count(label),label)
        for token in ("ctx.mmu.write8(", "ctx.mmu.write16(", "ctx.mmu.write32(",
                      "ipc70_ram.write8(", "ipc70_bus.write32(",
                      "scheduler.service_one(ctx.msr)", "ipc70_bus.tick("):
            self.assertEqual(self.before.count(token),self.after.count(token),token)
        self.assertNotIn("ctx.mmu.write",FOLLOWUP)
        self.assertNotIn("ipc70_bus.write",FOLLOWUP)

    def test_inherited_checkpoints_are_kept_but_accept_valid_native_pc(self):
        self.assertGreaterEqual(len(PAIR.findall(self.before)),7)
        self.assertEqual(len(PAIR.findall(self.after)),len(PAIR.findall(self.before))
        for marker in ("V166 second SC reply nested interrupt restore did not reach real guest call",
                       "V178 original SC reply burst did not reach bounded native checkpoint",
                       "V179 original SC reply continuation did not enter next PPC callee"):
            end=self.after.index('"'+marker+'");')
            start=self.after.rfind("check(",0,end)
            self.assertIn("v180_next_seen==1u",self.after[start:end])
        with self.assertRaises(ValueError):
            derive("invalid")
        with self.assertRaises(ValueError):
            widen_prior("invalid")

    def test_runner_validates_all_sixteen_original_trials(self):
        shell=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        self.assertIn("derive_v180_sc_reply_next_harness.py",shell)
        self.assertIn("V178_SC_BURST verified=1",shell)
        self.assertIn("V179_SC_NEXT verified=1",shell)
        self.assertIn("V180_SC_NEXT verified=1",shell)
        self.assertIn('trap \'rm -rf -- "$work"\' EXIT',shell)
        good=("V180_SC_NEXT clean=1 reply=1 queue=1 guest=1 "
              "caller=1 coherent=1 mapped=1 before=1 status=1 "
              "changed=0 pc=80545128 lr=80519850")
        self.assertTrue(re.fullmatch(PASS,good))
        self.assertFalse(re.fullmatch(PASS,good.replace("guest=1","guest=0")))
        self.assertTrue(re.fullmatch(PATTERN,good.replace("clean=1","clean=0")))
        with tempfile.TemporaryDirectory() as td:
            sh=Path(td)/"run.sh"
            sh.write_text(shell,encoding="utf-8")
            subprocess.run(["bash","-n",str(sh)],check=True)

    def test_private_owner_staging_and_cleanup(self):
        wf=(HERE.parents[1]/".github/workflows/wii-v180-sc-reply-next.yml").read_text(encoding="utf-8")
        self.assertIn("run_v180_sc_reply_next.sh",wf)
        self.assertIn("V180_SC_NEXT verified=1",wf)
        self.assertIn("  cancel-in-progress: false",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)

if __name__=="__main__":
    unittest.main()
