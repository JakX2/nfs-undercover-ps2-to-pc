#!/usr/bin/env python3
"""Original-free V166 second SC Y1 OSRestore and pending reply safety."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from derive_v165_sc_y1_post_osdi_harness import derive as previous
from derive_v166_sc_post_restore_harness import (
    derive, STATE, RESET, STOP, CONTINUE, OBSERVER,
    TRACE_ANCHOR, V165_FINAL, V166_FINAL, V165_CHECK, V166_CHECK,
    V165_TRIAL_END, V166_TRIAL_END, PREVIOUS_TRIAL, NEXT_TRIAL,
)
from derive_v166_sc_post_restore_runner import derive as runner, PASS

HERE=Path(__file__).resolve().parent

class V166(unittest.TestCase):
    def setUp(self):
        self.base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")

    def test_original_restore_execution_and_exact_prior_route(self):
        old=previous(self.base)
        new=derive(self.base)
        for marker in (STATE,RESET,STOP,TRACE_ANCHOR,V165_FINAL,
                       V165_CHECK,PREVIOUS_TRIAL):
            self.assertEqual(old.count(marker),1,marker[:70])
        self.assertEqual(PREVIOUS_TRIAL.count(V165_TRIAL_END),1)
        self.assertNotIn(STOP,new)
        self.assertIn(CONTINUE,new)
        self.assertIn(OBSERVER,new)
        self.assertIn(NEXT_TRIAL,new)
        self.assertEqual(new.count(V166_FINAL),1)
        self.assertEqual(new.count(V166_CHECK),1)
        self.assertEqual(new.count(V166_TRIAL_END),1)
        self.assertNotIn(V165_FINAL,new)
        self.assertNotIn(V165_CHECK,new)
        self.assertIn("addr==INT_RESTORE&&ctx.lr==0x8052941cu",CONTINUE)
        self.assertIn("return; // execute original OSRestoreInterrupts guest body",CONTINUE)
        self.assertIn("ctx.inst_count>v166_start_inst",OBSERVER)
        self.assertIn("ctx.gpr[13]==v147_first_r13",OBSERVER)
        self.assertIn("v166_target_pc=addr;v166_target_lr=ctx.lr;",OBSERVER)
        self.assertIn("IOS::Device::File",OBSERVER)
        self.assertIn("queued_replies()==0u",OBSERVER)
        self.assertIn("Mail::Y1",OBSERVER)
        self.assertIn("Irq::IPC_PPC",OBSERVER)
        self.assertIn("ready==(ee&&ipc70_bus.external_irq_level())",OBSERVER)
        self.assertIn("const bool ipc=addr==0x80519318u",OBSERVER)

    def test_no_forged_guest_registers_or_extra_ios_service(self):
        old=previous(self.base)
        new=derive(self.base)
        for key in ("ctx.mmu.write8(", "ctx.mmu.write16(", "ctx.mmu.write32(",
                    "ipc70_ram.write8(", "ipc70_bus.write32(",
                    "scheduler.service_one(ctx.msr)", "ipc70_bus.tick(",
                    "enter_external_irq("):
            self.assertEqual(old.count(key),new.count(key),key)
        for regex in (r"ctx\.gpr\[[^\]]+\]\s*=(?!=)",r"ctx\.msr\s*=(?!=)",
                      r"ctx\.srr0\s*=(?!=)",r"ctx\.srr1\s*=(?!=)"):
            self.assertEqual(len(re.findall(regex,old)),len(re.findall(regex,new)),regex)

    def test_sixteen_native_trials_and_private_cleanup(self):
        runner_script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for marker in ("derive_v166_sc_post_restore_harness.py",
                       "V164_SC_Y1_NESTED verified=1",
                       "V165_SC_POST_OSDI verified=1",
                       "V166_SC_POST_RESTORE verified=1",
                       'test "$(grep -Ec'):
            self.assertIn(marker,runner_script)
        good=("V166_SC_POST_RESTORE irq=1 reply=1 guest=1 call=1 coherent=1 "
              "ee=0 ready=0 ipc=1 helper=0 pc=80519318 lr=80526ca4")
        self.assertTrue(re.fullmatch(PASS,good))
        self.assertFalse(re.fullmatch(PASS,good.replace("reply=1","reply=0")))
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/"run.sh"
            p.write_text(runner_script,encoding="utf-8")
            subprocess.run(["bash","-n",str(p)],check=True)
        with self.assertRaises(ValueError):derive("invalid")
        with self.assertRaises(ValueError):runner("invalid")
        wf=(HERE.parents[1]/".github/workflows/wii-v166-sc-post-restore.yml").read_text(encoding="utf-8")
        self.assertIn("run_v166_sc_post_restore.sh",wf)
        self.assertIn("V166_SC_POST_RESTORE verified=1",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)

if __name__=="__main__":
    unittest.main()
