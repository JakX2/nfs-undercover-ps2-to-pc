#!/usr/bin/env python3
"""V178 original-free six-call guest burst, SDA and hardware safety tests."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v177_sc_reply_next_harness import derive as previous
from derive_v178_sc_reply_burst_harness import (
    derive, STATE, RESET, STOP, CONTINUE, OBSERVATION, TRACE_ANCHOR,
    PREVIOUS_TRIAL, NEXT_TRIAL, PAIR, widen_prior, MAX_CALLS,
    V111_ACTIVE, V111_SCOPED, V98_ACTIVE, V98_SCOPED,
    V83_ACTIVE, V83_SCOPED,
)
from derive_v178_sc_reply_burst_runner import derive as runner, PASS, TRACE

HERE=Path(__file__).resolve().parent

class V178(unittest.TestCase):
    def setUp(self):
        self.base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")

    def test_run_only_verified_original_callee_and_bound_calls(self):
        before=previous(self.base)
        after=derive(self.base)
        for marker in (STATE,RESET,STOP,TRACE_ANCHOR,PREVIOUS_TRIAL):
            self.assertEqual(before.count(marker),1,marker[:75])
        self.assertNotIn(STOP,after)
        self.assertIn(CONTINUE,after)
        self.assertIn(OBSERVATION,after)
        self.assertIn(NEXT_TRIAL,after)
        self.assertEqual(MAX_CALLS,6)
        self.assertIn("addr==0x80545100u&&ctx.lr==0x804f1e40u",CONTINUE)
        self.assertIn("const uint32_t v178_sc=ctx.gpr[13]-3176u",CONTINUE)
        self.assertIn("ctx.mmu.read8(v178_sc)==1u",CONTINUE)
        self.assertIn("return; // execute original 0x80545100",CONTINUE)
        self.assertNotIn("const uint32_t sc=",CONTINUE)
        self.assertIn("v178_trace_pc[v178_calls]=addr",OBSERVATION)
        self.assertIn("v178_trace_lr[v178_calls]=ctx.lr",OBSERVATION)
        self.assertIn("v178_calls<6u",OBSERVATION)
        self.assertIn("if(v178_calls<6u&&!changed)",OBSERVATION)
        self.assertIn("const bool changed=status!=v178_status_before",OBSERVATION)
        self.assertIn("ctx.inst_count>v178_last_inst",OBSERVATION)
        self.assertIn("v178_last_inst=ctx.inst_count",OBSERVATION)
        self.assertEqual(after.count("V178_SC_BURST calls="),1)
        self.assertEqual(after.count("V178_SC_TRACE step="),1)

    def test_v111_first_phase_copy_stays_verified_but_not_reapplied_to_reply(self):
        before=previous(self.base)
        after=derive(self.base)
        self.assertEqual(before.count(V111_ACTIVE),1)
        self.assertEqual(after.count(V111_SCOPED),1)
        self.assertNotIn(V111_ACTIVE,after)
        self.assertIn("post111_open==0u",V111_SCOPED)
        self.assertEqual(before.count("++post111_copy;return true;"),
                         after.count("++post111_copy;return true;"))
        self.assertEqual(before.count("++post111_open;post90_target=addr;"),
                         after.count("++post111_open;post90_target=addr;"))

    def test_v98_nand_registration_completes_once_and_never_replays_in_reply(self):
        before=previous(self.base)
        after=derive(self.base)
        self.assertEqual(before.count(V98_ACTIVE),1)
        self.assertEqual(after.count(V98_SCOPED),1)
        self.assertNotIn(V98_ACTIVE,after)
        self.assertIn("post98_return==0u",V98_SCOPED)
        self.assertEqual(before.count("++post98_return;"),
                         after.count("++post98_return;"))
        self.assertEqual(before.count("V98 unexpected NAND registration dependency"),
                         after.count("V98 unexpected NAND registration dependency"))

    def test_v83_synchronous_open_observer_is_phase_limited(self):
        before=previous(self.base)
        after=derive(self.base)
        self.assertEqual(before.count(V83_ACTIVE),1)
        self.assertEqual(after.count(V83_SCOPED),1)
        self.assertNotIn(V83_ACTIVE,after)
        self.assertIn("open83_second==0u",V83_SCOPED)
        # V83 must still detect its original second STM open.
        for marker in ('++open83_second;', 
                       'V83 first original IOS_Open did not return to next STM open',
                       'V83 unexpected original synchronous submit continuation dependency',
                       '++open83_free_restore;'):
            self.assertEqual(before.count(marker),after.count(marker),marker)

    def test_only_authentic_guest_pc_lr_endpoints_widen_preceding_trials(self):
        before=previous(self.base)
        after=derive(self.base)
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
            "V177 original SC reply handler callee did not enter subsequent native function",
        ):
            marker='"'+label+'");'
            self.assertEqual(after.count(marker),1)
            end=after.index(marker)
            start=after.rfind("check(",0,end)
            self.assertIn("v178_burst_seen==1u",after[start:end])
        with self.assertRaises(ValueError):derive("invalid")
        with self.assertRaises(ValueError):widen_prior("invalid")

    def test_no_guest_mutations_ios_pump_forged_callback_or_irq(self):
        before=previous(self.base)
        after=derive(self.base)
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

    def test_sixteen_owner_trials_and_private_cleaning(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for marker in ("derive_v178_sc_reply_burst_harness.py",
                       "V176_SC_REPLY_NEXT verified=1",
                       "V177_SC_REPLY_NEXT verified=1",
                       "V178_SC_BURST verified=1",
                       'test "$(grep -Ec',
                       'test "$trace_count" -ge 16',
                       'test "$trace_count" -le 96'):
            self.assertIn(marker,script)
        good=("V178_SC_BURST calls=6 clean=1 reply=1 guest=1 "
              "caller=1 coherent=1 mapped=1 before=1 status=1 changed=0 "
              "pc=805229b4 lr=80545120")
        self.assertTrue(re.fullmatch(PASS,good))
        self.assertTrue(re.fullmatch(PASS,good.replace("calls=6","calls=2").replace("status=1 changed=0","status=0 changed=1")))
        self.assertFalse(re.fullmatch(PASS,good.replace("calls=6","calls=7")))
        self.assertFalse(re.fullmatch(PASS,good.replace("guest=1","guest=0")))
        self.assertTrue(re.fullmatch(TRACE,"V178_SC_TRACE step=6 pc=805229b4 lr=80545120"))
        self.assertFalse(re.fullmatch(TRACE,"V178_SC_TRACE step=7 pc=805229b4 lr=80545120"))
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/"runner.sh"
            p.write_text(script,encoding="utf-8")
            subprocess.run(["bash","-n",str(p)],check=True)
        with self.assertRaises(ValueError):runner("invalid")
        wf=(HERE.parents[1]/".github/workflows/wii-v178-sc-reply-burst.yml").read_text(encoding="utf-8")
        self.assertIn("run_v178_sc_reply_burst.sh",wf)
        self.assertIn("V178_SC_BURST verified=1",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)

if __name__=="__main__":
    unittest.main()
