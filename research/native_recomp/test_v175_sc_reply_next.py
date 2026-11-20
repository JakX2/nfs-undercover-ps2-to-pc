#!/usr/bin/env python3
"""Original-free V175 SYSCONF reply continuation, native trial safety tests."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v174_sc_post_reply_helper_harness import derive as previous
from derive_v175_sc_reply_next_harness import (
    derive, STATE, RESET, STOP, CONTINUE, OBSERVATION, TRACE_ANCHOR,
    PREVIOUS_TRIAL, NEXT_TRIAL, PAIR, widen_prior,
)
from derive_v175_sc_reply_next_runner import derive as runner, PASS

HERE=Path(__file__).resolve().parent

class V175(unittest.TestCase):
    def setUp(self):
        self.base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")

    def test_guest_code_continues_from_authenticated_reply_successor(self):
        old=previous(self.base)
        new=derive(self.base)
        for anchor in (STATE,RESET,STOP,TRACE_ANCHOR,PREVIOUS_TRIAL):
            self.assertEqual(old.count(anchor),1,anchor[:75])
        self.assertNotIn(STOP,new)
        self.assertIn(CONTINUE,new)
        self.assertIn(OBSERVATION,new)
        self.assertIn(NEXT_TRIAL,new)
        self.assertEqual(new.count("V175_SC_REPLY_NEXT clean="),1)
        self.assertIn("addr==0x80522af4u&&ctx.lr==0x80519290u",CONTINUE)
        self.assertIn("ctx.mmu.read8(v175_sc)==1u",CONTINUE)
        self.assertIn("const uint32_t v175_sc=ctx.gpr[13]-3176u;",CONTINUE)
        self.assertNotIn("const uint32_t sc=ctx.gpr[13]-3176u;",CONTINUE)
        self.assertIn("v175_sda_before=ctx.mmu.read8(v175_sc)",CONTINUE)
        self.assertIn("return; // execute the original 0x80522AF4",CONTINUE)
        self.assertIn("ctx.inst_count>v175_start_inst",OBSERVATION)
        self.assertIn("ctx.gpr[13]==v147_first_r13",OBSERVATION)
        self.assertIn("((*control&Mail::Y1)==0u)",OBSERVATION)
        self.assertIn("((*flags&Irq::IPC_PPC)==0u)",OBSERVATION)
        self.assertIn("const bool changed=mapped&&status!=v175_sda_before",OBSERVATION)
        self.assertIn("v175_target_pc=addr;v175_target_lr=ctx.lr",OBSERVATION)

    def test_retain_prior_trial_proofs_and_fail_closed(self):
        old=previous(self.base)
        new=derive(self.base)
        self.assertGreaterEqual(len(PAIR.findall(old)),7)
        for label in (
            "V166 second SC reply nested interrupt restore did not reach real guest call",
            "V167 original SC reply IPC handler did not reach first real guest leaf",
            "V168 original SC Y1 register read did not reach second guest leaf",
            "V169 original SC reply processor did not reach next guest call",
            "V170 original SC Y1 reply read did not reach next native function",
            "V171 original SC reply processor did not reach distinct native callee",
            "V172 original SC Y1 reply PPCCTRL ACK was not performed by game code",
            "V173 original SYSCONF Y1 reply W1C did not advance to next guest call",
            "V174 original Wii SC reply follow-up did not call next native helper",
        ):
            marker='"'+label+'");'
            self.assertEqual(new.count(marker),1)
            end=new.index(marker)
            start=new.rfind("check(",0,end)
            self.assertIn("v175_next_seen==1u",new[start:end])
        with self.assertRaises(ValueError):derive("invalid")
        with self.assertRaises(ValueError):widen_prior("invalid")

    def test_no_synthetic_ppc_cpu_ios_status_or_interrupt_writes(self):
        old=previous(self.base)
        new=derive(self.base)
        for token in ("ctx.mmu.write8(", "ctx.mmu.write16(", "ctx.mmu.write32(",
                      "ipc70_ram.write8(", "ipc70_bus.write32(",
                      "scheduler.service_one(ctx.msr)", "ipc70_bus.tick(",
                      "enter_external_irq("):
            self.assertEqual(old.count(token),new.count(token),token)
        for pattern in (r"ctx\.gpr\[[^\]]+\]\s*=(?!=)",
                        r"ctx\.msr\s*=(?!=)",r"ctx\.srr0\s*=(?!=)",
                        r"ctx\.srr1\s*=(?!=)"):
            self.assertEqual(len(re.findall(pattern,old)),
                             len(re.findall(pattern,new)),pattern)

    def test_runner_16_trials_preserve_reply_and_cleanup(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for marker in ("derive_v175_sc_reply_next_harness.py",
                       "V173_SC_AFTER_Y1_ACK verified=1",
                       "V174_SC_POST_REPLY_HELPER verified=1",
                       "V175_SC_REPLY_NEXT verified=1",
                       'test "$(grep -Ec'):
            self.assertIn(marker,script)
        good=("V175_SC_REPLY_NEXT clean=1 wire=1 queue=1 guest=1 "
              "caller=1 coherent=1 mapped=1 before=1 status=1 changed=0 "
              "pc=8051905c lr=80522b20")
        self.assertTrue(re.fullmatch(PASS,good))
        self.assertTrue(re.fullmatch(PASS,good.replace("status=1 changed=0","status=0 changed=1")))
        for bad in ("clean=0","guest=0","mapped=0","queue=0"):
            self.assertFalse(re.fullmatch(PASS,good.replace(bad.replace("=0","=1"),bad)))
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/"run.sh";p.write_text(script,encoding="utf-8")
            subprocess.run(["bash","-n",str(p)],check=True)
        with self.assertRaises(ValueError):runner("invalid")
        wf=(HERE.parents[1]/".github/workflows/wii-v175-sc-reply-next.yml").read_text(encoding="utf-8")
        self.assertIn("run_v175_sc_reply_next.sh",wf)
        self.assertIn("V175_SC_REPLY_NEXT verified=1",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)

if __name__=="__main__":
    unittest.main()
