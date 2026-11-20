#!/usr/bin/env python3
"""Original-free V163 second reply IRQ timebase to scheduler disable guards."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v162_sc_reply_next_harness import derive as previous
from derive_v163_sc_y1_disable_harness import (
    derive, STATE, RESET, STOP, CONTINUE, OBSERVATION,
    PREVIOUS_TRIAL, NEXT_TRIAL, TRACE_ANCHOR
)
from derive_v163_sc_y1_disable_runner import derive as runner, PASS

HERE=Path(__file__).resolve().parent

class V163(unittest.TestCase):
    def setUp(self):
        self.base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")

    def test_release_only_owner_verified_timebase_helper(self):
        old=previous(self.base)
        new=derive(self.base)
        for anchor in (STATE,RESET,STOP,PREVIOUS_TRIAL,TRACE_ANCHOR):
            self.assertEqual(old.count(anchor),1,anchor[:70])
        self.assertNotIn(STOP,new)
        self.assertIn(CONTINUE,new)
        self.assertIn(OBSERVATION,new)
        self.assertIn(NEXT_TRIAL,new)
        self.assertIn("addr==0x8052a824u&&ctx.lr==0x80526c84u",CONTINUE)
        self.assertIn("return; // execute real Wii timebase guest helper",CONTINUE)
        self.assertIn("addr==0x805293f8u",OBSERVATION)
        self.assertIn("ctx.lr==0x80526c98u",OBSERVATION)
        self.assertIn("ctx.inst_count>v163_start_inst",OBSERVATION)
        self.assertIn("ctx.gpr[13]==v147_first_r13",OBSERVATION)
        self.assertIn("ipc70_bus.services().queued_replies()==0u",OBSERVATION)
        self.assertIn("IOS::Device::File",OBSERVATION)
        self.assertIn("Mail::Y1",OBSERVATION)
        self.assertIn("Irq::IPC_PPC",OBSERVATION)
        self.assertEqual(new.count("V163_SC_Y1_DISABLE irq="),1)

    def test_no_guest_or_hardware_mutations(self):
        old=previous(self.base)
        new=derive(self.base)
        for t in ("ctx.mmu.write8(", "ctx.mmu.write16(", "ctx.mmu.write32(",
                  "ipc70_ram.write8(", "ipc70_bus.write32(",
                  "scheduler.service_one(ctx.msr)", "ipc70_bus.tick(",
                  "enter_external_irq("):
            self.assertEqual(old.count(t),new.count(t),t)
        for pattern in (r"ctx\.gpr\[[^\]]+\]\s*=(?!=)",
                        r"ctx\.msr\s*=(?!=)",r"ctx\.srr0\s*=(?!=)",
                        r"ctx\.srr1\s*=(?!=)"):
            self.assertEqual(len(re.findall(pattern,old)),len(re.findall(pattern,new)),pattern)

    def test_sixteen_owner_original_trials_and_prior_checkpoints(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for t in ("derive_v163_sc_y1_disable_harness.py",
                  "V160_SC_VECTOR_HANDLER verified=1",
                  "V161_SC_Y1_DISPATCH verified=1",
                  "V162_SC_REPLY_NEXT verified=1",
                  "V163_SC_Y1_DISABLE verified=1",
                  'test "$(grep -Fxc'):
            self.assertIn(t,script)
        self.assertEqual(PASS,
            "V163_SC_Y1_DISABLE irq=1 reply=1 masked=1 guest=1 caller=1 pc=805293f8 lr=80526c98")
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"run.sh";p.write_text(script,encoding="utf-8")
            subprocess.run(["bash","-n",str(p)],check=True)
        with self.assertRaises(ValueError):derive("invalid")
        with self.assertRaises(ValueError):runner("invalid")
        wf=(HERE.parents[1]/".github/workflows/wii-v163-sc-y1-disable.yml").read_text(encoding="utf-8")
        self.assertIn("run_v163_sc_y1_disable.sh",wf)
        self.assertIn("V163_SC_Y1_DISABLE verified=1",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)

if __name__=="__main__":
    unittest.main()
