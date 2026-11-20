#!/usr/bin/env python3
"""Original-free V165 real guest nested OSDI and IOS reply safety checks."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from derive_v164_sc_y1_nested_helper_harness import derive as previous
from derive_v165_sc_after_osdi_harness import (
    derive, STATE, RESET, STOP, CONTINUE, OBSERVATION,
    TRACE_ANCHOR, V164_FINAL, V165_FINAL,
    V164_NEXT_PC, V165_NEXT_PC, PREVIOUS_TRIAL, NEXT_TRIAL,
)
from derive_v165_sc_after_osdi_runner import derive as runner, PASS

HERE=Path(__file__).resolve().parent

class V165(unittest.TestCase):
    def setUp(self):
        self.base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")

    def test_inherits_strict_v164_and_executes_real_osdi(self):
        before=previous(self.base)
        after=derive(self.base)
        for x in (STATE,RESET,STOP,V164_FINAL,TRACE_ANCHOR,PREVIOUS_TRIAL):
            self.assertEqual(before.count(x),1,x[:70])
        self.assertEqual(PREVIOUS_TRIAL.count(V164_NEXT_PC),1)
        self.assertNotIn(STOP,after)
        self.assertIn(CONTINUE,after)
        self.assertIn(OBSERVATION,after)
        self.assertIn(NEXT_TRIAL,after)
        self.assertEqual(after.count(V165_FINAL),1)
        self.assertEqual(after.count(V165_NEXT_PC),1)
        self.assertNotIn(V164_FINAL,after)
        self.assertIn("addr==0x805265acu&&ctx.lr==0x8052940cu",CONTINUE)
        self.assertIn("return; // execute authentic nested OSDisableInterrupts",CONTINUE)
        self.assertIn("ctx.inst_count>v165_start_inst",OBSERVATION)
        self.assertIn("ctx.gpr[13]==v147_first_r13",OBSERVATION)
        self.assertIn("ctx.lr>=0x80526a3cu&&ctx.lr<0x80529434u",OBSERVATION)
        self.assertIn("const bool restore=addr==INT_RESTORE",OBSERVATION)
        self.assertIn("IOS::Device::File",OBSERVATION)
        self.assertIn("queued_replies()==0u",OBSERVATION)
        self.assertIn("Mail::Y1",OBSERVATION)
        self.assertIn("Irq::IPC_PPC",OBSERVATION)

    def test_no_forged_guest_registers_irq_or_ios_pump(self):
        before=previous(self.base)
        after=derive(self.base)
        for marker in ("ctx.mmu.write8(", "ctx.mmu.write16(", "ctx.mmu.write32(",
                       "ipc70_ram.write8(", "ipc70_bus.write32(",
                       "scheduler.service_one(ctx.msr)", "ipc70_bus.tick(",
                       "enter_external_irq("):
            self.assertEqual(before.count(marker),after.count(marker),marker)
        for pattern in (r"ctx\.gpr\[[^\]]+\]\s*=(?!=)",r"ctx\.msr\s*=(?!=)",
                        r"ctx\.srr0\s*=(?!=)",r"ctx\.srr1\s*=(?!=)"):
            self.assertEqual(len(re.findall(pattern,before)),
                             len(re.findall(pattern,after)),pattern)

    def test_owner_original_16_trials_and_private_cleanup(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for marker in ("derive_v165_sc_after_osdi_harness.py",
                       "V163_SC_Y1_DISABLE verified=1",
                       "V164_SC_Y1_NESTED verified=1",
                       "V165_SC_AFTER_OSDI verified=1",
                       'test "$(grep -Ec'):
            self.assertIn(marker,script)
        good=("V165_SC_AFTER_OSDI irq=1 reply=1 guest=1 masked=1 call=1 "
              "restore=1 pc=805265d4 lr=8052941c")
        self.assertTrue(re.fullmatch(PASS,good))
        self.assertFalse(re.fullmatch(PASS,good.replace("reply=1","reply=0")))
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"run.sh"
            p.write_text(script,encoding="utf-8")
            subprocess.run(["bash","-n",str(p)],check=True)
        with self.assertRaises(ValueError):derive("invalid")
        with self.assertRaises(ValueError):runner("invalid")
        wf=(HERE.parents[1]/".github/workflows/wii-v165-sc-after-osdi.yml").read_text(encoding="utf-8")
        self.assertIn("run_v165_sc_after_osdi.sh",wf)
        self.assertIn("V165_SC_AFTER_OSDI verified=1",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)

if __name__=="__main__":
    unittest.main()
