#!/usr/bin/env python3
"""Original-free V157 SC rescheduler next-call and reply IRQ safety tests."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from derive_v156_sc_after_restore_harness import derive as previous
from derive_v157_sc_rescheduler_next_harness import (
    derive, STATE, RESET, STOP, CONTINUE, NEXT_OBSERVER,
    PREVIOUS_TRIAL, NEXT_TRIAL, V146_ONCE,
)
from derive_v157_sc_rescheduler_next_runner import derive as runner, PASS

HERE=Path(__file__).resolve().parent

class V157(unittest.TestCase):
    def setUp(self):
        self.source=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")

    def test_release_only_owner_verified_rescheduler(self):
        before=previous(self.source)
        after=derive(self.source)
        for anchor in (STATE, RESET, STOP, PREVIOUS_TRIAL, V146_ONCE):
            self.assertEqual(before.count(anchor),1,anchor[:80])
        self.assertNotIn(STOP,after)
        self.assertIn(CONTINUE,after)
        self.assertIn(NEXT_OBSERVER,after)
        self.assertIn(NEXT_TRIAL,after)
        self.assertIn("addr==0x80529940u&&ctx.lr==0x80526cb4u",CONTINUE)
        self.assertIn("ctx.inst_count>v157_first_inst",NEXT_OBSERVER)
        self.assertIn("ctx.gpr[13]==v147_first_r13",NEXT_OBSERVER)
        self.assertIn("V157Ios::Device::File",NEXT_OBSERVER)
        self.assertIn("V157Mail::Y1",NEXT_OBSERVER)
        self.assertIn("V157Irq::IPC_PPC",NEXT_OBSERVER)
        self.assertIn("ready==(ee&&ipc70_bus.external_irq_level())",NEXT_OBSERVER)
        self.assertEqual(after.count("V157_SC_RESCHED_NEXT y1="),1)
        self.assertNotIn("addr==0x80529718u",CONTINUE)

    def test_no_guest_or_ios_mutation(self):
        before=previous(self.source)
        after=derive(self.source)
        for tok in ("ctx.mmu.write8(", "ctx.mmu.write16(", "ctx.mmu.write32(",
                    "ipc70_ram.write8(", "ipc70_bus.write32(", "ipc70_bus.tick(",
                    "scheduler.service_one(ctx.msr)", "v139_scheduler.service_one("):
            self.assertEqual(before.count(tok),after.count(tok),tok)
        for pattern in (r"ctx\.gpr\[[^\]]+\]\s*=(?!=)",
                        r"ctx\.cr\[0\]\.eq\s*=(?!=)",
                        r"ctx\.msr\s*=(?!=)"):
            self.assertEqual(len(re.findall(pattern,before)),len(re.findall(pattern,after)),pattern)

    def test_sixteen_owner_trials_and_ee_unbiased(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for m in ("derive_v157_sc_rescheduler_next_harness.py",
                  "V155_SC_AFTER_DISABLE verified=1",
                  "V156_SC_AFTER_RESTORE verified=1",
                  "V157_SC_RESCHED_NEXT verified=1",
                  'test "$(grep -Ec'):
            self.assertIn(m,script)
        for x in ("0","1"):
            self.assertTrue(re.fullmatch(PASS,
                f"V157_SC_RESCHED_NEXT y1=1 reply=1 progressed=1 target=1 coherent=1 ee={x} ready={x} pc=80529718 lr=80526cb4"))
        self.assertFalse(re.fullmatch(PASS,
            "V157_SC_RESCHED_NEXT y1=0 reply=1 progressed=1 target=1 coherent=1 ee=0 ready=0 pc=80529718 lr=80526cb4"))
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"runner.sh"
            p.write_text(script,encoding="utf-8")
            subprocess.run(["bash","-n",str(p)],check=True)

    def test_fail_closed_and_private_cleanup(self):
        with self.assertRaises(ValueError):derive("invalid")
        with self.assertRaises(ValueError):runner("invalid")
        wf=(HERE.parents[1]/".github/workflows/wii-v157-sc-rescheduler-next.yml").read_text(encoding="utf-8")
        self.assertIn("run_v157_sc_rescheduler_next.sh",wf)
        self.assertIn("V157_SC_RESCHED_NEXT verified=1",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)

if __name__=="__main__":
    unittest.main()
