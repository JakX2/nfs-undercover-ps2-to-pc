#!/usr/bin/env python3
"""V165 original-free second reply IRQ post-OSDI guest successor tests."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from derive_v164_sc_y1_nested_helper_harness import derive as previous
from derive_v165_sc_y1_post_osdi_harness import (
    derive, STATE, RESET, STOP, CONTINUE, OBSERVER, TRACE_ANCHOR,
    PREVIOUS_TRIAL, NEXT_TRIAL, V164_FINAL, V165_FINAL,
    V164_CHECK, V165_CHECK,
)
from derive_v165_sc_y1_post_osdi_runner import derive as runner, PASS

HERE=Path(__file__).resolve().parent

class V165(unittest.TestCase):
    def setUp(self):
        self.base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")

    def test_runs_verified_original_nested_osdi_and_observes_next_call(self):
        old=previous(self.base)
        new=derive(self.base)
        for anchor in (STATE,RESET,STOP,PREVIOUS_TRIAL,V164_FINAL,V164_CHECK,TRACE_ANCHOR):
            self.assertEqual(old.count(anchor),1,anchor[:77])
        self.assertNotIn(STOP,new)
        self.assertIn(CONTINUE,new)
        self.assertIn(OBSERVER,new)
        self.assertIn(NEXT_TRIAL,new)
        self.assertEqual(new.count(V165_FINAL),1)
        self.assertEqual(new.count(V165_CHECK),1)
        self.assertNotIn(V164_FINAL,new)
        self.assertNotIn(V164_CHECK,new)
        self.assertEqual(new.count("V165_SC_POST_OSDI irq="),1)
        self.assertIn("addr==INT_DISABLE&&ctx.lr==0x8052940cu",CONTINUE)
        self.assertIn("return; // run original interrupt-disable helper body",CONTINUE)
        self.assertIn("ctx.inst_count>v165_start_inst",OBSERVER)
        self.assertIn("ctx.gpr[13]==v147_first_r13",OBSERVER)
        self.assertIn("v165_target_pc=addr;v165_target_lr=ctx.lr",OBSERVER)
        self.assertIn("addr==0x80519318u",OBSERVER)
        self.assertIn("addr==INT_DISABLE||addr==INT_RESTORE",OBSERVER)
        self.assertIn("queued_replies()==0u",OBSERVER)
        self.assertIn("Mail::Y1",OBSERVER)
        self.assertIn("Irq::IPC_PPC",OBSERVER)
        self.assertIn("IOS::Device::File",OBSERVER)

    def test_preserves_first_irq_observers_and_does_not_mutate_cpu(self):
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
        for marker in ("++v143_time_seen;", "++v144_disable_seen;",
                       "++v145_ipc_seen;", "++v162_next_seen;"):
            self.assertEqual(before.count(marker),after.count(marker),marker)

    def test_sixteen_native_trials_allow_only_observed_next_target(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for token in ("derive_v165_sc_y1_post_osdi_harness.py",
                      "V163_SC_Y1_DISABLE verified=1",
                      "V164_SC_Y1_NESTED verified=1",
                      "V165_SC_POST_OSDI verified=1",
                      'test "$(grep -Ec'):
            self.assertIn(token,script)
        target=("V165_SC_POST_OSDI irq=1 reply=1 masked=1 guest=1 caller=1 "
                "ipc=1 helper=0 pc=80519318 lr=80526ca8")
        self.assertTrue(re.fullmatch(PASS,target))
        self.assertTrue(re.fullmatch(PASS,target.replace("ipc=1 helper=0","ipc=0 helper=1")))
        self.assertFalse(re.fullmatch(PASS,target.replace("irq=1","irq=0")))
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"runner.sh";p.write_text(script,encoding="utf-8")
            subprocess.run(["bash","-n",str(p)],check=True)

    def test_fail_closed_private_source_cleanup(self):
        with self.assertRaises(ValueError):derive("invalid")
        with self.assertRaises(ValueError):runner("invalid")
        wf=(HERE.parents[1]/".github/workflows/wii-v165-sc-y1-post-osdi.yml").read_text(encoding="utf-8")
        self.assertIn("run_v165_sc_y1_post_osdi.sh",wf)
        self.assertIn("V165_SC_POST_OSDI verified=1",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)

if __name__=="__main__":
    unittest.main()
