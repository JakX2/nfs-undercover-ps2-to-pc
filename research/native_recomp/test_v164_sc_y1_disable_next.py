#!/usr/bin/env python3
"""Original-free V164 guest scheduler nested-helper and inherited IRQ guards."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from derive_v163_sc_y1_disable_harness import derive as previous
from derive_v164_sc_y1_disable_next_harness import (
    derive, STATE, RESET, STOP, CONTINUE, OBSERVATION, TRACE_ANCHOR,
    FIRST_PHASE, SCOPED_PHASE, V163_END, V164_END, PREVIOUS_TRIAL, NEXT_TRIAL,
)
from derive_v164_sc_y1_disable_next_runner import derive as runner, PASS

HERE=Path(__file__).resolve().parent

class V164(unittest.TestCase):
    def setUp(self):
        self.base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")

    def test_only_verified_sc_scheduler_disable_continues(self):
        old=previous(self.base)
        new=derive(self.base)
        for key in (STATE,RESET,STOP,TRACE_ANCHOR,FIRST_PHASE,PREVIOUS_TRIAL):
            self.assertEqual(old.count(key),1,key[:70])
        self.assertNotIn(STOP,new)
        self.assertIn(CONTINUE,new)
        self.assertIn(OBSERVATION,new)
        self.assertIn(NEXT_TRIAL,new)
        self.assertIn(V164_END,new)
        self.assertNotIn(V163_END,new)
        self.assertIn("addr==0x805293f8u&&ctx.lr==0x80526c98u",CONTINUE)
        self.assertIn("ctx.lr>=0x805293f8u&&ctx.lr<0x80529434u",OBSERVATION)
        self.assertIn("ctx.inst_count>v164_start_inst",OBSERVATION)
        self.assertIn("ctx.gpr[13]==v147_first_r13",OBSERVATION)
        self.assertIn("IOS::Device::File",OBSERVATION)
        self.assertIn("queued_replies()==0u",OBSERVATION)
        self.assertIn("Mail::Y1",OBSERVATION)
        self.assertIn("Irq::IPC_PPC",OBSERVATION)
        self.assertEqual(new.count("V164_SC_DISABLE_NEXT irq="),1)

    def test_stale_first_irq_nested_assertion_is_only_phase_scoped(self):
        old=previous(self.base)
        new=derive(self.base)
        self.assertIn(SCOPED_PHASE,new)
        self.assertNotIn(FIRST_PHASE,new)
        self.assertIn("v161_dispatch_seen==0u",SCOPED_PHASE)
        self.assertEqual(old.count("V145 original SC dispatcher nested IRQ helper lost pending IOS state"),
                         new.count("V145 original SC dispatcher nested IRQ helper lost pending IOS state"))

    def test_no_new_guest_or_ios_state_writes(self):
        old=previous(self.base)
        new=derive(self.base)
        for key in ("ctx.mmu.write8(", "ctx.mmu.write16(", "ctx.mmu.write32(",
                    "ipc70_ram.write8(", "ipc70_bus.write32(",
                    "scheduler.service_one(ctx.msr)", "ipc70_bus.tick(",
                    "enter_external_irq("):
            self.assertEqual(old.count(key),new.count(key),key)
        for pat in (r"ctx\.gpr\[[^\]]+\]\s*=(?!=)",r"ctx\.msr\s*=(?!=)",
                    r"ctx\.srr0\s*=(?!=)",r"ctx\.srr1\s*=(?!=)"):
            self.assertEqual(len(re.findall(pat,old)),len(re.findall(pat,new)),pat)

    def test_native_runner_and_private_cleanup(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for m in ("derive_v164_sc_y1_disable_next_harness.py",
                  "V162_SC_REPLY_NEXT verified=1",
                  "V163_SC_Y1_DISABLE verified=1",
                  "V164_SC_DISABLE_NEXT verified=1",
                  'test "$(grep -Ec'):
            self.assertIn(m,script)
        example=("V164_SC_DISABLE_NEXT irq=1 reply=1 masked=1 stepped=1 caller=1 "
                 "pc=805265ac lr=80529408")
        self.assertTrue(re.fullmatch(PASS,example))
        self.assertFalse(re.fullmatch(PASS,example.replace("caller=1","caller=0")))
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/"run.sh"
            p.write_text(script,encoding="utf-8")
            subprocess.run(["bash","-n",str(p)],check=True)
        with self.assertRaises(ValueError):derive("invalid")
        with self.assertRaises(ValueError):runner("invalid")
        workflow=(HERE.parents[1]/".github/workflows/wii-v164-sc-y1-disable-next.yml").read_text(encoding="utf-8")
        self.assertIn("run_v164_sc_y1_disable_next.sh",workflow)
        self.assertIn("V164_SC_DISABLE_NEXT verified=1",workflow)
        self.assertEqual(workflow.count("      - name: Remove private owner and generated code"),1)

if __name__=="__main__":
    unittest.main()
