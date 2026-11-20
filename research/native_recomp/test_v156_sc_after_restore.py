#!/usr/bin/env python3
"""Original-free V156 guest restore-interrupt helper/source-only safety tests."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from derive_v155_sc_after_disable_harness import derive as previous
from derive_v156_sc_after_restore_harness import (
    derive, STATE, RESET, STOP, CONTINUE, NEXT_OBSERVER,
    PREVIOUS_TRIAL, NEXT_TRIAL, V146_ONCE
)
from derive_v156_sc_after_restore_runner import derive as runner, PASS

HERE=Path(__file__).resolve().parent

class V156(unittest.TestCase):
    def setUp(self):
        self.source=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")

    def test_executes_authentic_restore_interrupt_entry(self):
        prior=previous(self.source)
        new=derive(self.source)
        for anchor in (STATE,RESET,STOP,PREVIOUS_TRIAL,V146_ONCE):
            self.assertEqual(prior.count(anchor),1,anchor[:75])
        self.assertNotIn(STOP,new)
        self.assertIn(CONTINUE,new)
        self.assertIn(NEXT_OBSERVER,new)
        self.assertIn(NEXT_TRIAL,new)
        self.assertIn("addr==0x805265d4u&&ctx.lr==0x80529458u",CONTINUE)
        self.assertIn("ctx.inst_count>v156_first_inst",NEXT_OBSERVER)
        self.assertIn("ctx.gpr[13]==v147_first_r13",NEXT_OBSERVER)
        self.assertIn("V156Ios::Device::File",NEXT_OBSERVER)
        self.assertIn("V156Mail::Y1",NEXT_OBSERVER)
        self.assertIn("V156Irq::IPC_PPC",NEXT_OBSERVER)
        self.assertIn("ready==(ee&&ipc70_bus.external_irq_level())",NEXT_OBSERVER)
        self.assertEqual(new.count("V156_SC_AFTER_RESTORE irq="),1)

    def test_no_synthetic_guest_cpu_writes_or_ios_pumping(self):
        prior=previous(self.source)
        new=derive(self.source)
        for tok in ("ctx.mmu.write8(", "ctx.mmu.write16(", "ctx.mmu.write32(",
                    "ipc70_ram.write8(", "ipc70_bus.write32(", "ipc70_bus.tick(",
                    "scheduler.service_one(ctx.msr)", "v139_scheduler.service_one("):
            self.assertEqual(prior.count(tok),new.count(tok),tok)
        for pattern in (r"ctx\.gpr\[[^\]]+\]\s*=(?!=)",
                        r"ctx\.cr\[0\]\.eq\s*=(?!=)",
                        r"ctx\.msr\s*=(?!=)"):
            self.assertEqual(len(re.findall(pattern,prior)),len(re.findall(pattern,new)),pattern)

    def test_sixteen_trials_and_no_forced_ee_assumption(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for marker in ("derive_v156_sc_after_restore_harness.py",
                       "V153_SC_REPLY verified=1",
                       "V154_SC_SCHED_NEXT verified=1",
                       "V155_SC_AFTER_DISABLE verified=1",
                       "V156_SC_AFTER_RESTORE verified=1",
                       'test "$(grep -Ec'):
            self.assertIn(marker,script)
        for value in ("0","1"):
            self.assertTrue(re.fullmatch(PASS,
               f"V156_SC_AFTER_RESTORE irq=1 reply=1 progress=1 text=1 coherent=1 ee={value} ready={value} pc=80529940 lr=80526cb4"))
        self.assertFalse(re.fullmatch(PASS,
               "V156_SC_AFTER_RESTORE irq=0 reply=1 progress=1 text=1 coherent=1 ee=0 ready=0 pc=80529940 lr=80526cb4"))
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/"run.sh"
            p.write_text(script,encoding="utf-8")
            subprocess.run(["bash","-n",str(p)],check=True)

    def test_fail_closed_and_private_cleanup(self):
        with self.assertRaises(ValueError):derive("invalid")
        with self.assertRaises(ValueError):runner("invalid")
        wf=(HERE.parents[1]/".github/workflows/wii-v156-sc-after-restore.yml").read_text(encoding="utf-8")
        self.assertIn("run_v156_sc_after_restore.sh",wf)
        self.assertIn("V156_SC_AFTER_RESTORE verified=1",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)

if __name__=="__main__":
    unittest.main()
