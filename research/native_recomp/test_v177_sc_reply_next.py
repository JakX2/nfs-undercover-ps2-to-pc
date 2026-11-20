#!/usr/bin/env python3
"""Original-free V177 SYSCONF reply continuation and PowerPC safety tests."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v176_sc_reply_next_harness import derive as previous
from derive_v177_sc_reply_next_harness import (
    derive, STATE, RESET, STOP, CONTINUE, OBSERVATION, TRACE_ANCHOR,
    PREVIOUS_TRIAL, NEXT_TRIAL, PAIR, widen_prior,
)
from derive_v177_sc_reply_next_runner import derive as runner, PASS

HERE=Path(__file__).resolve().parent

class V177(unittest.TestCase):
    def setUp(self):
        self.source=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")

    def test_execute_original_authenticated_scy1_callee(self):
        prior=previous(self.source)
        new=derive(self.source)
        for marker in (STATE,RESET,STOP,TRACE_ANCHOR,PREVIOUS_TRIAL):
            self.assertEqual(prior.count(marker),1,marker[:65])
        self.assertNotIn(STOP,new)
        self.assertIn(CONTINUE,new)
        self.assertIn(OBSERVATION,new)
        self.assertIn(NEXT_TRIAL,new)
        self.assertEqual(new.count("V177_SC_REPLY_NEXT clean="),1)
        self.assertIn("addr==0x804f0e04u&&ctx.lr==0x805192acu",CONTINUE)
        self.assertIn("const uint32_t v177_sc=ctx.gpr[13]-3176u",CONTINUE)
        self.assertIn("ctx.mmu.read8(v177_sc)==1u",CONTINUE)
        self.assertIn("v177_sda_before=ctx.mmu.read8(v177_sc)",CONTINUE)
        self.assertNotIn("const uint32_t sc=",CONTINUE)
        self.assertIn("return; // execute original 0x804F0E04",CONTINUE)
        self.assertIn("ctx.inst_count>v177_start_inst",OBSERVATION)
        self.assertIn("ctx.gpr[13]==v147_first_r13",OBSERVATION)
        self.assertIn("const bool changed=mapped&&status!=v177_sda_before",OBSERVATION)
        self.assertIn("ctx.lr>=0x805190c0u&&ctx.lr<0x805194c4u",OBSERVATION)
        self.assertIn("v177_target_pc=addr;v177_target_lr=ctx.lr",OBSERVATION)

    def test_prior_guards_authenticate_only_actual_original_successor(self):
        before=previous(self.source)
        after=derive(self.source)
        self.assertGreaterEqual(len(PAIR.findall(before)),7)
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
            "V176 original SC reply callback frontier did not enter next guest function",
        ):
            marker='"'+label+'");'
            self.assertEqual(after.count(marker),1)
            end=after.index(marker)
            start=after.rfind("check(",0,end)
            self.assertIn("v177_next_seen==1u",after[start:end])
        with self.assertRaises(ValueError):derive("invalid")
        with self.assertRaises(ValueError):widen_prior("invalid")

    def test_no_synthetic_guest_writes_ios_callback_or_irq(self):
        before=previous(self.source)
        after=derive(self.source)
        for token in ("ctx.mmu.write8(", "ctx.mmu.write16(", "ctx.mmu.write32(",
                      "ipc70_ram.write8(", "ipc70_bus.write32(",
                      "scheduler.service_one(ctx.msr)", "ipc70_bus.tick(",
                      "enter_external_irq("):
            self.assertEqual(before.count(token),after.count(token),token)
        for pattern in (r"ctx\.gpr\[[^\]]+\]\s*=(?!=)",
                        r"ctx\.msr\s*=(?!=)",r"ctx\.srr0\s*=(?!=)",
                        r"ctx\.srr1\s*=(?!=)"):
            self.assertEqual(len(re.findall(pattern,before)),
                             len(re.findall(pattern,after)),pattern)

    def test_sixteen_original_trials_and_owner_cleanup(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for marker in ("derive_v177_sc_reply_next_harness.py",
                       "V175_SC_REPLY_NEXT verified=1",
                       "V176_SC_REPLY_NEXT verified=1",
                       "V177_SC_REPLY_NEXT verified=1",
                       'test "$(grep -Ec'):
            self.assertIn(marker,script)
        good=("V177_SC_REPLY_NEXT clean=1 wire=1 queue=1 guest=1 "
              "caller=1 coherent=1 mapped=1 before=1 status=1 "
              "changed=0 ipc=0 pc=805229b4 lr=804f0e30")
        self.assertTrue(re.fullmatch(PASS,good))
        self.assertTrue(re.fullmatch(PASS,good.replace("status=1 changed=0","status=0 changed=1")))
        self.assertFalse(re.fullmatch(PASS,good.replace("guest=1","guest=0")))
        self.assertFalse(re.fullmatch(PASS,good.replace("coherent=1","coherent=0")))
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"run.sh";p.write_text(script,encoding="utf-8")
            subprocess.run(["bash","-n",str(p)],check=True)
        with self.assertRaises(ValueError):runner("invalid")
        wf=(HERE.parents[1]/".github/workflows/wii-v177-sc-reply-next.yml").read_text(encoding="utf-8")
        self.assertIn("run_v177_sc_reply_next.sh",wf)
        self.assertIn("V177_SC_REPLY_NEXT verified=1",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)

if __name__=="__main__":
    unittest.main()
