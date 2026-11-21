#!/usr/bin/env python3
"""V184 owner-free Wii SC IPC second-request continuation regression gates."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v183_sc_reply_burst_harness import derive as previous
from derive_v184_sc_reply_burst_harness import (
    derive, STOP, CONTINUE, OBSERVER, PAIR, NEXT_TRIAL, MAX_CALLS,
    PREVIOUS_OBSERVER, widen_prior,
    V171_DISTINCT_EXCLUSION, V184_SCOPED_EXCLUSION,
)
from derive_v184_sc_reply_burst_runner import derive as runner, PASS, TRACE, ENTRY

HERE=Path(__file__).resolve().parent
class V184(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=previous(base)
        cls.after=derive(base)

    def test_exact_v183_authenticated_pc_lr_callee_is_executed(self):
        self.assertEqual(MAX_CALLS,6)
        self.assertIn(STOP,PREVIOUS_OBSERVER)
        self.assertIn(STOP,self.before)
        self.assertNotIn(STOP,self.after)
        self.assertIn(CONTINUE,self.after)
        self.assertIn("addr==0x8051ad3cu&&ctx.lr==0x805192c8u",CONTINUE)
        self.assertIn("v183_calls==8u&&v183_status_before==1u",CONTINUE)
        self.assertIn("v184_start_inst=ctx.inst_count",CONTINUE)
        self.assertIn("return; // execute original Wii 0x8051AD3C",CONTINUE)
        self.assertIn("v183_burst_seen==1u&&v184_burst_seen==0u",OBSERVER)
        self.assertIn("v184_calls<6u&&!changed",OBSERVER)
        self.assertIn(NEXT_TRIAL,self.after)

    def test_second_request_is_observed_without_fabricating_ios_service(self):
        self.assertIn("v183_second_msg==1u",CONTINUE)
        self.assertIn("v183_second_ctrl==1u",CONTINUE)
        self.assertIn("V184_IPC_ENTRY phase=1",CONTINUE)
        self.assertIn("v184_ctrl&Mail::X1",CONTINUE)
        for token in ("ctx.mmu.write8(", "ctx.mmu.write16(", "ctx.mmu.write32(",
                      "ipc70_ram.write8(", "ipc70_bus.write32(",
                      "scheduler.service_one(ctx.msr)", "ipc70_bus.tick("):
            self.assertEqual(self.before.count(token),self.after.count(token),token)
        for source in (CONTINUE,OBSERVER):
            self.assertNotIn("ctx.mmu.write",source)
            self.assertNotIn("ipc70_bus.write",source)
            self.assertNotIn("service_one(",source)
        for prior in ("V183_SECOND_MSG phase=1", "V183_SECOND_CTRL phase=1",
                      "V183_SC_BURST calls=", "V182_REQUEST_VECTOR entered=1",
                      "unexpected original IPC ACK MMIO write"):
            self.assertEqual(self.before.count(prior),self.after.count(prior),prior)

    def test_prior_pc_lr_gates_remain_verified(self):
        self.assertGreaterEqual(len(PAIR.findall(self.before)),7)
        self.assertEqual(len(PAIR.findall(self.before)),len(PAIR.findall(self.after)))
        for label in ("V182 original SC reply call burst did not reach authenticated native stop",
                      "V183 original SC reply IPC followup did not reach bounded guest call"):
            end=self.after.index('"'+label+'");')
            start=self.after.rfind("check(",0,end)
            self.assertIn("v184_burst_seen==1u",self.after[start:end])
        with self.assertRaises(ValueError):derive("invalid")
        with self.assertRaises(ValueError):widen_prior("invalid")

    def test_v171_original_distinct_exclusion_only_scopes_after_v184(self):
        self.assertEqual(self.before.count(V171_DISTINCT_EXCLUSION),1)
        self.assertEqual(self.after.count(V184_SCOPED_EXCLUSION),1)
        self.assertIn("c.pc!=0x8051905cu",V184_SCOPED_EXCLUSION)
        self.assertIn("nwii::runtime::v184_burst_seen==1u",V184_SCOPED_EXCLUSION)
        self.assertNotIn("v183_burst_seen==1u",V184_SCOPED_EXCLUSION)
        self.assertIn(
            "V171 original SC reply processor did not reach distinct native callee",
            self.after)

    def test_sixteen_original_trials_and_result_contract(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text(encoding="utf-8"))
        self.assertIn("derive_v184_sc_reply_burst_harness.py",script)
        self.assertIn("V183_SC_BURST verified=1",script)
        self.assertIn("V184_SC_BURST verified=1",script)
        self.assertIn('trap \'rm -rf -- "$work"\' EXIT',script)
        good=("V184_SC_BURST calls=6 clean=1 reply=1 queue=1 guest=1 "
              "caller=1 coherent=1 mapped=1 submitted=1 before=1 "
              "status=1 changed=0 pc=8051ad38 lr=805192e0")
        self.assertTrue(re.fullmatch(PASS,good))
        self.assertTrue(re.fullmatch(TRACE,"V184_SC_TRACE step=6 pc=8051ad38 lr=805192e0"))
        self.assertTrue(re.fullmatch(ENTRY,"V184_IPC_ENTRY phase=1 msg=1 ctrl=1 x1=1 known=1 calls=8"))
        self.assertFalse(re.fullmatch(PASS,good.replace("calls=6","calls=7")))
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/"runner.sh"
            path.write_text(script,encoding="utf-8")
            subprocess.run(["bash","-n",str(path)],check=True)

    def test_owner_assertion_id_maps_only_public_label(self):
        from diagnose_v184_sc_reply_burst import describe
        from classify_v38_native_failure import STRING
        labels=sorted(set(STRING.findall(self.after)))
        self.assertGreater(len(labels),588)
        self.assertEqual(describe(588),labels[587])
        with self.assertRaises(ValueError):describe(0)
        with self.assertRaises(ValueError):describe(99999)
        source=(HERE/"diagnose_v184_sc_reply_burst.py").read_text(encoding="utf-8")
        self.assertNotIn("print(raw)",source)
        self.assertNotIn("print(word)",source)
        self.assertNotIn("ipc70_ram.read32",source)

    def test_owner_ci_private_cleanup(self):
        wf=(HERE.parents[1]/".github/workflows/wii-v184-sc-reply-burst.yml").read_text()
        self.assertIn("run_v184_sc_reply_burst.sh",wf)
        self.assertIn("V184_SC_BURST verified=1",wf)
        self.assertIn("  cancel-in-progress: false",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)

if __name__=="__main__":
    unittest.main()
