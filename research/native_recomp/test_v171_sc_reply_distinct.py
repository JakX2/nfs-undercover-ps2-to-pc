#!/usr/bin/env python3
"""V171 owner-free bounded real SC Y1 read-loop / distinct guest proof."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v170_sc_reply_read_harness import derive as previous
from derive_v171_sc_reply_distinct_harness import (
    derive, STATE, RESET, STOP, CONTINUE, OBSERVER, TRACE_ANCHOR,
    PREVIOUS_TRIAL, NEXT_TRIAL, PAIR, widen_prior_pc_gates,
)
from derive_v171_sc_reply_distinct_runner import derive as runner, PASS
HERE=Path(__file__).resolve().parent

class V171(unittest.TestCase):
    def setUp(self):
        self.base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")

    def test_authentic_read_loop_is_bounded_and_next_callee_is_distinct(self):
        prior=previous(self.base)
        actual=derive(self.base)
        for anchor in (STATE,RESET,STOP,TRACE_ANCHOR,PREVIOUS_TRIAL):
            self.assertEqual(prior.count(anchor),1,anchor[:70])
        self.assertNotIn(STOP,actual)
        self.assertIn(CONTINUE,actual)
        self.assertIn(OBSERVER,actual)
        self.assertIn(NEXT_TRIAL,actual)
        self.assertIn("addr==0x8051905cu&&ctx.lr==0x805190fcu",CONTINUE)
        self.assertIn("v171_start_inst=ctx.inst_count",CONTINUE)
        self.assertIn("if(addr==0x8051905cu)",OBSERVER)
        self.assertIn("if(v171_read_count>32u)",OBSERVER)
        self.assertIn("check(false,\"V171 authentic SC Y1 read helper loop exceeded budget\")",OBSERVER)
        self.assertIn("return; // perform another original PPC read",OBSERVER)
        self.assertIn("ctx.pc==addr&&ctx.inst_count>v171_start_inst",OBSERVER)
        self.assertIn("ctx.mmu.get_ptr(sc_addr)",OBSERVER)
        self.assertIn("ctx.mmu.read8(sc_addr)",OBSERVER)
        self.assertIn("const bool changed=mapped&&status!=1u",OBSERVER)
        self.assertEqual(actual.count("V171_SC_DISTINCT guest="),1)
        self.assertEqual(actual.count("V171_SC_READ_LIMIT count="),1)

    def test_all_prior_native_pc_gates_keep_state_and_admit_only_distinct_target(self):
        actual=derive(self.base)
        for label in (
            "V166 second SC reply nested interrupt restore did not reach real guest call",
            "V167 original SC reply IPC handler did not reach first real guest leaf",
            "V168 original SC Y1 register read did not reach second guest leaf",
            "V169 original SC reply processor did not reach next guest call",
            "V170 original SC Y1 reply read did not reach next native function",
        ):
            marker='"'+label+'");'
            self.assertEqual(actual.count(marker),1,label)
            end=actual.index(marker)
            start=actual.rfind("check(",0,end)
            self.assertGreaterEqual(start,0)
            check=actual[start:end]
            self.assertIn("v171_distinct_seen==1u",check)
            self.assertIn("c.pc==nwii::runtime::v171_target_pc",check)
            self.assertIn("c.lr==nwii::runtime::v171_target_lr",check)
            self.assertIn("!c.is_running",check)
        self.assertIn("c.pc!=0x8051905cu",NEXT_TRIAL)
        self.assertIn("V171 original SC reply processor did not reach distinct native callee",actual)
        with self.assertRaises(ValueError):widen_prior_pc_gates("invalid")
        self.assertTrue(PAIR.search("c.pc==nwii::runtime::v170_target_pc&&c.lr==nwii::runtime::v170_target_lr"))

    def test_read_only_cpu_irq_and_ios_state(self):
        before=previous(self.base)
        after=derive(self.base)
        for marker in ("ctx.mmu.write8(", "ctx.mmu.write16(", "ctx.mmu.write32(",
                       "ipc70_ram.write8(", "ipc70_bus.write32(",
                       "ipc70_bus.tick(", "scheduler.service_one(ctx.msr)",
                       "enter_external_irq("):
            self.assertEqual(before.count(marker),after.count(marker),marker)
        for pattern in (r"ctx\.gpr\[[^\]]+\]\s*=(?!=)",r"ctx\.msr\s*=(?!=)",
                        r"ctx\.srr0\s*=(?!=)",r"ctx\.srr1\s*=(?!=)"):
            self.assertEqual(len(re.findall(pattern,before)),
                             len(re.findall(pattern,after)),pattern)

    def test_sixteen_owner_trials_and_private_cleanup(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for marker in ("derive_v171_sc_reply_distinct_harness.py",
                       "V169_SC_REPLY_NEXT verified=1",
                       "V170_SC_REPLY_NEXT verified=1",
                       "V171_SC_DISTINCT verified=1",
                       'test "$(grep -Ec'):
            self.assertIn(marker,script)
        good=("V171_SC_DISTINCT guest=1 caller=1 coherent=1 mapped=1 "
              "y1=1 irq=1 wire=1 reply=1 status=1 changed=0 write=1 "
              "reads=3 pc=8051906c lr=80519110")
        self.assertTrue(re.fullmatch(PASS,good))
        self.assertFalse(re.fullmatch(PASS,good.replace("guest=1","guest=0")))
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"runner.sh";p.write_text(script,encoding="utf-8")
            subprocess.run(["bash","-n",str(p)],check=True)
        with self.assertRaises(ValueError):derive("invalid")
        with self.assertRaises(ValueError):runner("invalid")
        workflow=(HERE.parents[1]/".github/workflows/wii-v171-sc-reply-distinct.yml").read_text(encoding="utf-8")
        self.assertIn("run_v171_sc_reply_distinct.sh",workflow)
        self.assertIn("V171_SC_DISTINCT verified=1",workflow)
        self.assertEqual(workflow.count("      - name: Remove private owner and generated code"),1)
if __name__=="__main__":
    unittest.main()
