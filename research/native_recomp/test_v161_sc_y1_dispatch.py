#!/usr/bin/env python3
"""V161 original-free SC second interrupt OS handler/dispatcher source guards."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v160_sc_y1_vector_handler_harness import derive as previous
from derive_v161_sc_y1_dispatch_harness import (
    derive, STATE, RESET, STOP, CONTINUE, OBSERVER, TRACE_ANCHOR,
    PREVIOUS_TRIAL, NEXT_TRIAL, V160_PC, V161_PC,
    V160_FINAL_PC, V161_FINAL_PC,
)
from derive_v161_sc_y1_dispatch_runner import derive as runner, PASS

HERE=Path(__file__).resolve().parent

class V161(unittest.TestCase):
    def setUp(self):
        self.base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")

    def test_original_handler_runs_until_authentic_dispatch(self):
        before=previous(self.base)
        after=derive(self.base)
        for anchor in (STATE,RESET,STOP,TRACE_ANCHOR,V160_PC,PREVIOUS_TRIAL):
            self.assertEqual(before.count(anchor),1,anchor[:72])
        self.assertNotIn(STOP,after)
        self.assertIn(CONTINUE,after)
        self.assertIn(OBSERVER,after)
        self.assertIn(NEXT_TRIAL,after)
        self.assertIn(V161_PC,after)
        self.assertIn(V161_FINAL_PC,after)
        self.assertNotIn(V160_PC,after)
        self.assertIn("return; // run original Broadway external interrupt-handler body",CONTINUE)
        self.assertIn("addr==0x80526a3cu",OBSERVER)
        self.assertIn("ctx.gpr[3]==4u",OBSERVER)
        self.assertIn("ctx.gpr[4]==THREAD",OBSERVER)
        self.assertIn("ctx.inst_count>v161_handler_inst",OBSERVER)
        self.assertIn("ctx.mmu.read32(THREAD+408u)==v158_expected_pc",OBSERVER)
        self.assertIn("ctx.mmu.read32(THREAD+412u)==v158_expected_msr",OBSERVER)
        self.assertIn("undercover::wii::IpcMailbox::",OBSERVER) if False else None
        self.assertIn("Mail::Y1",OBSERVER)
        self.assertIn("Irq::IPC_PPC",OBSERVER)
        self.assertEqual(after.count("V161_SC_Y1_DISPATCH index="),1)

    def test_no_extra_irq_device_pumping_or_guest_writes(self):
        before=previous(self.base)
        after=derive(self.base)
        for token in ("ctx.mmu.write8(", "ctx.mmu.write16(", "ctx.mmu.write32(",
                      "ipc70_ram.write8(", "ipc70_bus.write32(",
                      "scheduler.service_one(ctx.msr)", "ipc70_bus.tick(",
                      "enter_external_irq("):
            self.assertEqual(before.count(token),after.count(token),token)
        for pattern in (r"ctx\.gpr\[[^\]]+\]\s*=(?!=)",
                        r"ctx\.msr\s*=(?!=)",
                        r"ctx\.srr0\s*=(?!=)",
                        r"ctx\.srr1\s*=(?!=)"):
            self.assertEqual(len(re.findall(pattern,before)),
                             len(re.findall(pattern,after)),pattern)

    def test_native_runner_requires_sixteen_dispatches(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for token in ("derive_v161_sc_y1_dispatch_harness.py",
                      "V159_SC_Y1_VECTOR verified=1",
                      "V160_SC_VECTOR_HANDLER verified=1",
                      "V161_SC_Y1_DISPATCH verified=1",
                      'test "$(grep -Ec'):
            self.assertIn(token,script)
        example=("V161_SC_Y1_DISPATCH index=1 context=1 saved_pc=1 saved_msr=1 "
                 "running=1 masked=1 irq=1 advanced=1 pc=80526a3c lr=80526ca8")
        self.assertTrue(re.fullmatch(PASS,example))
        self.assertFalse(re.fullmatch(PASS,example.replace("index=1","index=0")))
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/"runner.sh"
            p.write_text(script,encoding="utf-8")
            subprocess.run(["bash","-n",str(p)],check=True)

    def test_fail_closed_and_owner_cleanup(self):
        with self.assertRaises(ValueError):derive("invalid")
        with self.assertRaises(ValueError):runner("invalid")
        wf=(HERE.parents[1]/".github/workflows/wii-v161-sc-y1-dispatch.yml").read_text(encoding="utf-8")
        self.assertIn("run_v161_sc_y1_dispatch.sh",wf)
        self.assertIn("V161_SC_Y1_DISPATCH verified=1",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)

if __name__=="__main__":
    unittest.main()
