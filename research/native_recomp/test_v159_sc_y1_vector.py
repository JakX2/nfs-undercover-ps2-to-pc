#!/usr/bin/env python3
"""Original-free V159 host exception entry from authentic SC reply RFI tests."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v158_sc_rfi_restore_harness import derive as previous
from derive_v159_sc_y1_vector_harness import (
    derive, STOP, CONTINUE, RFI_OBSERVER, STATE, RESET,
    PREVIOUS_TRIAL, NEXT_TRIAL, V154_CHECK, VECTOR_GATE,
)
from derive_v159_sc_y1_vector_runner import derive as runner, PASS

HERE=Path(__file__).resolve().parent

class V159(unittest.TestCase):
    def setUp(self):
        self.source=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")

    def test_pending_irq_enters_original_installed_vector_after_rfi(self):
        prior=previous(self.source)
        actual=derive(self.source)
        for needle in (STATE,RESET,STOP,PREVIOUS_TRIAL):
            self.assertEqual(prior.count(needle),1,needle[:70])
        self.assertNotIn(STOP,actual)
        self.assertIn(CONTINUE,actual)
        self.assertIn(NEXT_TRIAL,actual)
        self.assertEqual(prior.count(V154_CHECK),1)
        self.assertIn(VECTOR_GATE,actual)
        self.assertNotIn(V154_CHECK,actual)
        self.assertIn("c.pc==undercover::wii::ExternalVector",VECTOR_GATE)
        self.assertIn("c.srr0==nwii::runtime::v158_expected_pc",VECTOR_GATE)
        self.assertIn("c.srr1==(nwii::runtime::v158_expected_msr&",VECTOR_GATE)
        self.assertIn("ipc70_bus.external_exception_pending(ctx.msr)",CONTINUE)
        self.assertIn("!ctx.dispatch_saved_ctx",CONTINUE)
        self.assertIn("v158_selected_thread",CONTINUE)
        self.assertIn("enter_external_irq(",CONTINUE)
        self.assertIn("irq74_vector,true",CONTINUE)
        self.assertIn("undercover::wii::ExternalVector",CONTINUE)
        self.assertIn("ctx.srr0==original_pc",CONTINUE)
        self.assertIn("ctx.srr1==(original_msr&undercover::wii::ExternalSrr1Mask)",CONTINUE)
        self.assertIn("ctx.msr==(original_msr&~undercover::wii::ExternalMsrClear)",CONTINUE)
        self.assertIn("ctx.gpr==original_gprs",CONTINUE)
        self.assertIn("!ipc70_bus.external_exception_pending(ctx.msr)",CONTINUE)
        self.assertEqual(actual.count("V159_SC_Y1_VECTOR pending="),1)

    def test_no_fabricated_cpu_changes_and_one_hardware_exception_entry(self):
        old=previous(self.source)
        actual=derive(self.source)
        for tok in ("ctx.mmu.write8(", "ctx.mmu.write16(", "ctx.mmu.write32(",
                    "ipc70_ram.write8(", "ipc70_bus.write32(",
                    "ipc70_bus.tick(", "scheduler.service_one(ctx.msr)",
                    "v139_scheduler.service_one("):
            self.assertEqual(old.count(tok),actual.count(tok),tok)
        for pattern in (r"ctx\.gpr\[[^\]]+\]\s*=(?!=)",
                        r"ctx\.cr\[0\]\.eq\s*=(?!=)",
                        r"ctx\.msr\s*=(?!=)",
                        r"ctx\.srr0\s*=(?!=)",
                        r"ctx\.srr1\s*=(?!=)"):
            self.assertEqual(len(re.findall(pattern,old)),len(re.findall(pattern,actual)),pattern)
        self.assertEqual(actual.count("enter_external_irq("),
                         old.count("enter_external_irq(")+1)
        self.assertIn("ctx.is_running=false;throw ExceptionStop{};",CONTINUE)

    def test_native_runner_retains_all_prior_gates_and_sixteen_trials(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for token in ("derive_v159_sc_y1_vector_harness.py",
                      "V157_SC_RESCHED_NEXT verified=1",
                      "V158_SC_RFI verified=1",
                      "V159_SC_Y1_VECTOR verified=1",
                      'test "$(grep -Fxc'):
            self.assertIn(token,script)
        self.assertTrue(re.fullmatch(
            r"V159_SC_Y1_VECTOR pending=1 safe=1 entered=1 vector=1 regs=1 masked=1",
            PASS))
        self.assertNotIn("pending=0",PASS)
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/"runner.sh";p.write_text(script,encoding="utf-8")
            subprocess.run(["bash","-n",str(p)],check=True)

    def test_fail_closed_and_private_cleanup(self):
        with self.assertRaises(ValueError):derive("invalid")
        with self.assertRaises(ValueError):runner("invalid")
        wf=(HERE.parents[1]/".github/workflows/wii-v159-sc-y1-vector.yml").read_text(encoding="utf-8")
        self.assertIn("run_v159_sc_y1_vector.sh",wf)
        self.assertIn("V159_SC_Y1_VECTOR verified=1",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)

if __name__=="__main__":
    unittest.main()
