#!/usr/bin/env python3
"""Original-free safety tests for original SC LoadContext RFI restoration."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from derive_v157_sc_rescheduler_next_harness import derive as previous
from derive_v158_sc_rfi_restore_harness import (
    derive, STATE, RESET, STOP, CONTINUE, CALLBACK_ANCHOR,
    RFI_OBSERVER, NEXT_TRIAL, PREVIOUS_TRIAL,
)
from derive_v158_sc_rfi_restore_runner import derive as runner, PASS

HERE=Path(__file__).resolve().parent

class V158(unittest.TestCase):
    def setUp(self):
        self.source=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")

    def test_only_authenticated_guest_context_load_continues(self):
        old=previous(self.source)
        new=derive(self.source)
        for anchor in (STATE,RESET,STOP,CALLBACK_ANCHOR,PREVIOUS_TRIAL):
            self.assertEqual(old.count(anchor),1,anchor[:75])
        self.assertNotIn(STOP,new)
        self.assertIn(CONTINUE,new)
        self.assertIn(RFI_OBSERVER,new)
        self.assertEqual(new.count("bool process_pending_callbacks(CPUContext& ctx){"),1)
        self.assertEqual(old.count("if(ack77_reply==1u&&reply79_irq==0u){"),
                         new.count("if(ack77_reply==1u&&reply79_irq==0u){"))
        self.assertNotIn("if(ack77_reply==1u&&reply79_irq==0u){",RFI_OBSERVER)
        self.assertIn(NEXT_TRIAL,new)
        self.assertIn("addr==0x805229b4u&&ctx.lr==0x80526cbcu",CONTINUE)
        self.assertIn("ctx.gpr[3]==IDLE_CONTEXT",CONTINUE)
        self.assertIn("V158_SC_LOAD_ENTRY route=1",CONTINUE)
        self.assertIn("ctx.pc==sched74_resume&&ctx.inst_count>v158_load_inst",RFI_OBSERVER)
        self.assertIn("ctx.msr==vector75_srr1",RFI_OBSERVER)
        self.assertIn("ctx.gpr==vector75_gprs",RFI_OBSERVER)
        self.assertIn("ctx.lr==vector75_lr",RFI_OBSERVER)
        self.assertIn("V158Ios::Device::File",RFI_OBSERVER)
        self.assertIn("V158Mail::Y1",RFI_OBSERVER)
        self.assertIn("V158Irq::IPC_PPC",RFI_OBSERVER)
        self.assertIn("ready==(ee&&ipc70_bus.external_irq_level())",RFI_OBSERVER)
        self.assertEqual(new.count("V158_SC_RFI pc="),1)

    def test_no_artificial_rfi_irq_or_ios_pump(self):
        before=previous(self.source)
        after=derive(self.source)
        for tok in ("ctx.mmu.write8(", "ctx.mmu.write16(", "ctx.mmu.write32(",
                    "ipc70_ram.write8(", "ipc70_bus.write32(", "ipc70_bus.tick(",
                    "scheduler.service_one(ctx.msr)", "v139_scheduler.service_one(",
                    "enter_external_irq("):
            self.assertEqual(before.count(tok),after.count(tok),tok)
        for pattern in (r"ctx\.gpr\[[^\]]+\]\s*=(?!=)",
                        r"ctx\.cr\[0\]\.eq\s*=(?!=)",
                        r"ctx\.msr\s*=(?!=)",
                        r"ctx\.srr0\s*=(?!=)",
                        r"ctx\.srr1\s*=(?!=)"):
            self.assertEqual(len(re.findall(pattern,before)),
                             len(re.findall(pattern,after)),pattern)

    def test_all_sixteen_rfi_trials_preserve_y1_and_prior_gates(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for marker in ("derive_v158_sc_rfi_restore_harness.py",
                       "V156_SC_AFTER_RESTORE verified=1",
                       "V157_SC_RESCHED_NEXT verified=1",
                       "V158_SC_RFI verified=1",
                       'test "$(grep -Ec',
                       'test "$(grep -Fxc'):
            self.assertIn(marker,script)
        for ee in ("0","1"):
            self.assertTrue(re.fullmatch(PASS,
                f"V158_SC_RFI pc=1 msr=1 regs=1 waiting=1 irq=1 reply=1 coherent=1 ee={ee} ready={ee}"))
        self.assertFalse(re.fullmatch(PASS,
                "V158_SC_RFI pc=1 msr=0 regs=1 waiting=1 irq=1 reply=1 coherent=1 ee=1 ready=1"))
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"runner.sh"
            p.write_text(script,encoding="utf-8")
            subprocess.run(["bash","-n",str(p)],check=True)

    def test_fail_closed_and_private_cleanup(self):
        with self.assertRaises(ValueError):derive("invalid")
        with self.assertRaises(ValueError):runner("invalid")
        wf=(HERE.parents[1]/".github/workflows/wii-v158-sc-rfi-restore.yml").read_text(encoding="utf-8")
        self.assertIn("run_v158_sc_rfi_restore.sh",wf)
        self.assertIn("V158_SC_RFI verified=1",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)

if __name__=="__main__":
    unittest.main()
