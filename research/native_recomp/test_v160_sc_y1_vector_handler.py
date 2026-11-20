#!/usr/bin/env python3
"""Original-free V160 SC Y1 guest vector to installed interrupt handler tests."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v159_sc_y1_vector_harness import derive as previous
from derive_v160_sc_y1_vector_handler_harness import (
    derive, STATE, RESET, STOP, CONTINUE, TRACE, TRACE_ANCHOR,
    PREVIOUS_TRIAL, NEXT_TRIAL, V159_PC, V160_PC,
)
from derive_v160_sc_y1_vector_handler_runner import derive as runner, ENTRY, PASS

HERE=Path(__file__).resolve().parent

class V160(unittest.TestCase):
    def setUp(self):
        self.original=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")

    def test_original_exception_vector_body_reaches_wii_handler(self):
        prior=previous(self.original)
        after=derive(self.original)
        for token in (STATE,RESET,STOP,TRACE_ANCHOR,PREVIOUS_TRIAL):
            self.assertEqual(prior.count(token),1,token[:75])
        self.assertNotIn(STOP,after)
        self.assertIn(CONTINUE,after)
        self.assertIn(TRACE,after)
        self.assertIn(NEXT_TRIAL,after)
        self.assertIn("return true; // allow native dispatcher",CONTINUE)
        self.assertIn("undercover::wii::ExternalVector",TRACE)
        self.assertIn("addr==0x80526ce0u",TRACE)
        self.assertIn("ctx.mmu.read8(undercover::wii::ExternalVector",TRACE)
        self.assertIn("irq74_vector[i]",TRACE)
        self.assertIn("ctx.srr0==v158_expected_pc",TRACE)
        self.assertIn("ctx.srr1==(v158_expected_msr&undercover::wii::ExternalSrr1Mask)",TRACE)
        self.assertIn("ctx.gpr==v158_expected_gprs",TRACE)
        self.assertIn("ctx.inst_count>v160_start_inst",TRACE)
        self.assertEqual(prior.count(V159_PC),1)
        self.assertNotIn(V159_PC,after)
        self.assertIn(V160_PC,after)
        self.assertEqual(after.count("V160_SC_VECTOR_ENTRY saved="),1)
        self.assertEqual(after.count("V160_SC_VECTOR_HANDLER vector="),1)

    def test_hardware_exception_occurs_once_and_does_not_forge_cpu_state(self):
        old=previous(self.original)
        after=derive(self.original)
        for token in ("ctx.mmu.write8(", "ctx.mmu.write16(", "ctx.mmu.write32(",
                      "ipc70_ram.write8(", "ipc70_bus.write32(", "ipc70_bus.tick(",
                      "scheduler.service_one(ctx.msr)", "enter_external_irq("):
            self.assertEqual(old.count(token),after.count(token),token)
        for pattern in (r"ctx\.gpr\[[^\]]+\]\s*=(?!=)",
                        r"ctx\.msr\s*=(?!=)",r"ctx\.srr0\s*=(?!=)",
                        r"ctx\.srr1\s*=(?!=)"):
            self.assertEqual(len(re.findall(pattern,old)),
                             len(re.findall(pattern,after)),pattern)
        self.assertIn("ctx.is_running=false;throw ExceptionStop{};",TRACE)
        self.assertIn("return; // allow original guest exception vector instructions",TRACE)

    def test_runner_retains_v158_v159_and_sixteen_native_proofs(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for token in ("derive_v160_sc_y1_vector_handler_harness.py",
                      "V158_SC_RFI verified=1",
                      "V159_SC_Y1_VECTOR verified=1",
                      "V160_SC_VECTOR_HANDLER verified=1",
                      'test "$(grep -Ec',
                      'test "$(grep -Fxc'):
            self.assertIn(token,script)
        self.assertEqual(ENTRY,"V160_SC_VECTOR_ENTRY saved=1 regs=1 bytes=1 masked=1")
        self.assertTrue(re.fullmatch(PASS,
            "V160_SC_VECTOR_HANDLER vector=1 masked=1 irq=1 advanced=1 pc=80526ce0 lr=80000528"))
        self.assertFalse(re.fullmatch(PASS,
            "V160_SC_VECTOR_HANDLER vector=0 masked=1 irq=1 advanced=1 pc=80526ce0 lr=80000528"))
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"runner.sh";p.write_text(script,encoding="utf-8")
            subprocess.run(["bash","-n",str(p)],check=True)

    def test_fail_closed_and_remove_private_owner(self):
        with self.assertRaises(ValueError):derive("invalid")
        with self.assertRaises(ValueError):runner("invalid")
        wf=(HERE.parents[1]/".github/workflows/wii-v160-sc-y1-vector-handler.yml").read_text(encoding="utf-8")
        self.assertIn("run_v160_sc_y1_vector_handler.sh",wf)
        self.assertIn("V160_SC_VECTOR_HANDLER verified=1",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)

if __name__=="__main__":
    unittest.main()
