#!/usr/bin/env python3
"""Original-free V176 SC callback-frontier and native PowerPC safety tests."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v175_sc_reply_next_harness import derive as previous
from derive_v176_sc_reply_next_harness import (
    derive, STATE, RESET, STOP, CONTINUE, OBSERVATION, TRACE_ANCHOR,
    PREVIOUS_TRIAL, NEXT_TRIAL, PAIR, widen_prior,
)
from derive_v176_sc_reply_next_runner import derive as runner, PASS

HERE=Path(__file__).resolve().parent

class V176(unittest.TestCase):
    def setUp(self):
        self.original=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")

    def test_original_0x805228cc_execution_and_guest_selected_next_call(self):
        old=previous(self.original)
        new=derive(self.original)
        for marker in (STATE, RESET, STOP, TRACE_ANCHOR, PREVIOUS_TRIAL):
            self.assertEqual(old.count(marker),1,marker[:70])
        self.assertNotIn(STOP,new)
        self.assertIn(CONTINUE,new)
        self.assertIn(OBSERVATION,new)
        self.assertIn(NEXT_TRIAL,new)
        self.assertEqual(new.count("V176_SC_REPLY_NEXT clean="),1)
        self.assertIn("addr==0x805228ccu&&ctx.lr==0x80519298u",CONTINUE)
        self.assertIn("const uint32_t v176_sc=ctx.gpr[13]-3176u",CONTINUE)
        self.assertIn("ctx.mmu.read8(v176_sc)==1u",CONTINUE)
        self.assertIn("v176_sda_before=ctx.mmu.read8(v176_sc)",CONTINUE)
        self.assertIn("return; // execute original Wii 0x805228CC",CONTINUE)
        self.assertNotIn("const uint32_t sc=",CONTINUE)
        self.assertIn("ctx.inst_count>v176_start_inst",OBSERVATION)
        self.assertIn("ctx.gpr[13]==v147_first_r13",OBSERVATION)
        self.assertIn("const bool changed=mapped&&status!=v176_sda_before",OBSERVATION)
        self.assertIn("const bool osinit=addr==0x8052096cu",OBSERVATION)
        self.assertIn("v176_target_pc=addr;v176_target_lr=ctx.lr",OBSERVATION)

    def test_prior_gates_keep_genuine_original_pc_lr_and_status_ownership(self):
        old=previous(self.original)
        new=derive(self.original)
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
            "V175 original SC reply successor did not reach new PPC callee",
        ):
            marker='"'+label+'");'
            self.assertEqual(new.count(marker),1)
            finish=new.index(marker)
            start=new.rfind("check(",0,finish)
            self.assertIn("v176_next_seen==1u",new[start:finish])
        with self.assertRaises(ValueError):derive("invalid")
        with self.assertRaises(ValueError):widen_prior("invalid")

    def test_no_forced_sda_guest_writes_ios_or_external_irq(self):
        old=previous(self.original)
        new=derive(self.original)
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

    def test_sixteen_trial_runner_and_private_cleanup(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for marker in ("derive_v176_sc_reply_next_harness.py",
                       "V174_SC_POST_REPLY_HELPER verified=1",
                       "V175_SC_REPLY_NEXT verified=1",
                       "V176_SC_REPLY_NEXT verified=1",
                       'test "$(grep -Ec'):
            self.assertIn(marker,script)
        example=("V176_SC_REPLY_NEXT clean=1 wire=1 queue=1 guest=1 "
                 "caller=1 coherent=1 mapped=1 before=1 status=1 "
                 "changed=0 osinit=0 pc=805228cc lr=80519298")
        self.assertTrue(re.fullmatch(PASS,example))
        self.assertTrue(re.fullmatch(PASS,example.replace("status=1 changed=0","status=0 changed=1")))
        self.assertFalse(re.fullmatch(PASS,example.replace("guest=1","guest=0")))
        self.assertFalse(re.fullmatch(PASS,example.replace("mapped=1","mapped=0")))
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/"run.sh"
            p.write_text(script,encoding="utf-8")
            subprocess.run(["bash","-n",str(p)],check=True)
        with self.assertRaises(ValueError):runner("invalid")
        wf=(HERE.parents[1]/".github/workflows/wii-v176-sc-reply-next.yml").read_text(encoding="utf-8")
        self.assertIn("run_v176_sc_reply_next.sh",wf)
        self.assertIn("V176_SC_REPLY_NEXT verified=1",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)

if __name__=="__main__":
    unittest.main()
