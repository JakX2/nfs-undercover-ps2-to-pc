#!/usr/bin/env python3
"""V174 original-free post-Y1 reply guest successor and SC byte safeguards."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v173_sc_after_y1_ack_harness import derive as previous
from derive_v174_sc_post_reply_helper_harness import (
    derive, STATE, RESET, STOP, CONTINUE, OBSERVATION, TRACE_ANCHOR,
    PREVIOUS_TRIAL, NEXT_TRIAL, PAIR, widen_prior,
)
from derive_v174_sc_post_reply_helper_runner import derive as runner, PASS

HERE=Path(__file__).resolve().parent

class V174(unittest.TestCase):
    def setUp(self):
        self.base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")

    def test_original_reply_successor_proceeds_without_sda_patch(self):
        old=previous(self.base)
        new=derive(self.base)
        for anchor in (STATE,RESET,STOP,TRACE_ANCHOR,PREVIOUS_TRIAL):
            self.assertEqual(old.count(anchor),1,anchor[:70])
        self.assertNotIn(STOP,new)
        self.assertIn(CONTINUE,new)
        self.assertIn(OBSERVATION,new)
        self.assertIn(NEXT_TRIAL,new)
        self.assertEqual(new.count("V174_SC_POST_REPLY_HELPER cleared="),1)
        self.assertIn("addr==0x80522294u&&ctx.lr==0x80519124u",CONTINUE)
        self.assertIn("ctx.mmu.read8(sc)==1u",CONTINUE)
        self.assertIn("v174_sda_before=ctx.mmu.read8(sc)",CONTINUE)
        self.assertIn("return; // execute original 0x80522294",CONTINUE)
        self.assertIn("ctx.inst_count>v174_start_inst",OBSERVATION)
        self.assertIn("ctx.gpr[13]==v147_first_r13",OBSERVATION)
        self.assertIn("((*ctrl&Mail::Y1)==0u)",OBSERVATION)
        self.assertIn("((*flags&Irq::IPC_PPC)==0u)",OBSERVATION)
        self.assertIn("const bool changed=mapped&&status!=v174_sda_before",OBSERVATION)
        self.assertIn("v174_target_pc=addr;v174_target_lr=ctx.lr",OBSERVATION)

    def test_prior_checkpoints_accept_only_observed_v174_pc_and_lr(self):
        old=previous(self.base)
        new=derive(self.base)
        matches=PAIR.findall(old)
        self.assertGreaterEqual(len(matches),6)
        self.assertNotIn("c.pc==nwii::runtime::v173_target_pc&&\n             c.lr==nwii::runtime::v173_target_lr",new)
        for label in (
            "V166 second SC reply nested interrupt restore did not reach real guest call",
            "V167 original SC reply IPC handler did not reach first real guest leaf",
            "V168 original SC Y1 register read did not reach second guest leaf",
            "V169 original SC reply processor did not reach next guest call",
            "V170 original SC Y1 reply read did not reach next native function",
            "V171 original SC reply processor did not reach distinct native callee",
            "V172 original SC Y1 reply PPCCTRL ACK was not performed by game code",
            "V173 original SYSCONF Y1 reply W1C did not advance to next guest call",
        ):
            mark='"'+label+'");'
            self.assertEqual(new.count(mark),1)
            end=new.index(mark)
            start=new.rfind("check(",0,end)
            self.assertIn("v174_next_seen==1u",new[start:end])
        with self.assertRaises(ValueError):widen_prior("invalid")

    def test_no_synthetic_guest_cpu_ios_irq_or_sda_modifications(self):
        old=previous(self.base)
        new=derive(self.base)
        for token in ("ctx.mmu.write8(", "ctx.mmu.write16(", "ctx.mmu.write32(",
                      "ipc70_ram.write8(", "ipc70_bus.write32(",
                      "scheduler.service_one(ctx.msr)", "ipc70_bus.tick(",
                      "enter_external_irq("):
            self.assertEqual(old.count(token),new.count(token),token)
        for pattern in (r"ctx\.gpr\[[^\]]+\]\s*=(?!=)",
                        r"ctx\.msr\s*=(?!=)",
                        r"ctx\.srr0\s*=(?!=)",r"ctx\.srr1\s*=(?!=)"):
            self.assertEqual(len(re.findall(pattern,old)),
                             len(re.findall(pattern,new)),pattern)
        self.assertIn("nwii::runtime::v173_flag_ack_seen==1u",NEXT_TRIAL)

    def test_native_runner_sixteen_and_private_cleanup(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for token in ("derive_v174_sc_post_reply_helper_harness.py",
                      "V172_SC_Y1_ACK verified=1",
                      "V173_SC_AFTER_Y1_ACK verified=1",
                      "V174_SC_POST_REPLY_HELPER verified=1",
                      'test "$(grep -Ec'):
            self.assertIn(token,script)
        good=("V174_SC_POST_REPLY_HELPER cleared=1 reply=1 guest=1 "
              "caller=1 coherent=1 mapped=1 before=1 status=1 changed=0 "
              "pc=8051905c lr=805222c4")
        self.assertTrue(re.fullmatch(PASS,good))
        self.assertTrue(re.fullmatch(PASS,good.replace("status=1 changed=0","status=0 changed=1")))
        self.assertFalse(re.fullmatch(PASS,good.replace("cleared=1","cleared=0")))
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/"run.sh";p.write_text(script,encoding="utf-8")
            subprocess.run(["bash","-n",str(p)],check=True)
        with self.assertRaises(ValueError):derive("invalid")
        with self.assertRaises(ValueError):runner("invalid")
        wf=(HERE.parents[1]/".github/workflows/wii-v174-sc-post-reply-helper.yml").read_text(encoding="utf-8")
        self.assertIn("run_v174_sc_post_reply_helper.sh",wf)
        self.assertIn("V174_SC_POST_REPLY_HELPER verified=1",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)

if __name__=="__main__":
    unittest.main()
