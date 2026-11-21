#!/usr/bin/env python3
"""Original-free V185 Wii native IPC reply reader continuation tests."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v184_sc_reply_burst_harness import derive as previous
from derive_v185_sc_reply_next_harness import (
    derive, STOP, CONTINUE, OBSERVER, NEXT_TRIAL, PAIR, widen_prior,
)
from derive_v185_sc_reply_next_runner import derive as runner, PASS, ENTRY, PATTERN
HERE=Path(__file__).resolve().parent

class V185(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=previous(base)
        cls.after=derive(base)

    def test_continue_exact_authenticated_original_y1_reader(self):
        self.assertIn(STOP,self.before)
        self.assertNotIn(STOP,self.after)
        self.assertIn(CONTINUE,self.after)
        self.assertIn("addr==0x8051905cu&&ctx.lr==0x8051935cu",CONTINUE)
        self.assertIn("v184_calls==6u&&v184_status_before==1u",CONTINUE)
        self.assertIn("v185_start_inst=ctx.inst_count",CONTINUE)
        self.assertIn("return; // execute real original 0x8051905C",CONTINUE)
        self.assertIn("v184_burst_seen==1u&&v185_next_seen==0u",OBSERVER)
        self.assertIn("ctx.inst_count>v185_start_inst",OBSERVER)
        self.assertIn(NEXT_TRIAL,self.after)

    def test_only_observe_new_ios_open_not_synthesize_reply(self):
        self.assertIn("v183_second_msg==1u&&v183_second_ctrl==1u",CONTINUE)
        self.assertIn("V185_IPC_ENTRY phase=1",CONTINUE)
        self.assertIn("V185_SC_NEXT clean=",OBSERVER)
        self.assertIn("ipc70_ram.read32(v183_second_phys)==IOS::Reply",OBSERVER)
        for token in ("ctx.mmu.write8(", "ctx.mmu.write16(", "ctx.mmu.write32(",
                      "ipc70_ram.write8(", "ipc70_bus.write32(",
                      "scheduler.service_one(ctx.msr)", "ipc70_bus.tick("):
            self.assertEqual(self.before.count(token),self.after.count(token),token)
        for src in (CONTINUE,OBSERVER):
            for token in ("ctx.mmu.write", "ipc70_ram.write", "ipc70_bus.write32",
                          "scheduler.service_one(", "ipc70_bus.tick("):
                self.assertNotIn(token,src)
        for token in ("V184_SC_BURST calls=", "V183_SC_BURST calls=",
                      "V184_IPC_ENTRY phase=1", "V183_SECOND_MSG phase=1",
                      "V183_SECOND_CTRL phase=1", "V182_REQUEST_VECTOR entered=1"):
            self.assertEqual(self.before.count(token),self.after.count(token),token)

    def test_prior_guest_checkpoints_keep_strict_endpoint_rules(self):
        self.assertGreaterEqual(len(PAIR.findall(self.before)),7)
        self.assertEqual(len(PAIR.findall(self.before)),len(PAIR.findall(self.after)))
        for label in ("V171 original SC reply processor did not reach distinct native callee",
                      "V183 original SC reply IPC followup did not reach bounded guest call",
                      "V184 original SC reply continuation did not enter bounded native call"):
            end=self.after.index('"'+label+'");')
            start=self.after.rfind("check(",0,end)
            self.assertIn("v185_next_seen==1u",self.after[start:end])
        with self.assertRaises(ValueError):derive("invalid")
        with self.assertRaises(ValueError):widen_prior("invalid")

    def test_sixteen_owner_original_trials_with_bounded_safe_output(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text(encoding="utf-8"))
        self.assertIn("derive_v185_sc_reply_next_harness.py",script)
        self.assertIn("V184_SC_BURST verified=1",script)
        self.assertIn("V185_SC_NEXT verified=1",script)
        self.assertIn('trap \'rm -rf -- "$work"\' EXIT',script)
        good=("V185_SC_NEXT clean=1 x1=0 request=1 replied=0 queue=1 "
              "guest=1 caller=1 coherent=1 mapped=1 before=1 status=1 "
              "changed=0 pc=8051906c lr=8051936c")
        self.assertTrue(re.fullmatch(PASS,good))
        self.assertTrue(re.fullmatch(PATTERN,good.replace("guest=1","guest=0")))
        self.assertFalse(re.fullmatch(PASS,good.replace("guest=1","guest=0")))
        self.assertTrue(re.fullmatch(ENTRY,
            "V185_IPC_ENTRY phase=1 request=1 x1=0 y1=0 y2=0 open=1 replied=0 status=1"))
        with tempfile.TemporaryDirectory() as root:
            file=Path(root)/"run.sh";file.write_text(script,encoding="utf-8")
            subprocess.run(["bash","-n",str(file)],check=True)

    def test_owner_ci_sanitizes_private_data_and_cleans(self):
        wf=(HERE.parents[1]/".github/workflows/wii-v185-sc-reply-next.yml").read_text()
        self.assertIn("run_v185_sc_reply_next.sh",wf)
        self.assertIn("V185_SC_NEXT verified=1",wf)
        self.assertIn("  cancel-in-progress: false",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)

if __name__=="__main__":
    unittest.main()
