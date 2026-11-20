#!/usr/bin/env python3
"""V164 original-free Y1 reply nested scheduler helper and phase guard tests."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v163_sc_y1_disable_harness import derive as previous
from derive_v164_sc_y1_nested_helper_harness import (
    derive, STATE, RESET, STOP, CONTINUE, OBSERVER, TRACE_ANCHOR,
    PREVIOUS_TRIAL, NEXT_TRIAL, V163_FINAL, V164_FINAL,
    OLD_NESTED, SCOPED_NESTED, OLD_REGISTERED, SCOPED_REGISTERED,
    OLD_V144, SCOPED_V144,
)
from derive_v164_sc_y1_nested_helper_runner import derive as runner, PASS

HERE=Path(__file__).resolve().parent

class V164(unittest.TestCase):
    def setUp(self):
        self.base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")

    def test_original_sc_scheduler_disable_reaches_guest_nested_helper(self):
        old=previous(self.base)
        new=derive(self.base)
        for anchor in (STATE,RESET,STOP,TRACE_ANCHOR,PREVIOUS_TRIAL,V163_FINAL):
            self.assertEqual(old.count(anchor),1,anchor[:80])
        self.assertNotIn(STOP,new)
        self.assertIn(CONTINUE,new)
        self.assertIn(OBSERVER,new)
        self.assertIn(NEXT_TRIAL,new)
        self.assertEqual(new.count(V164_FINAL),1)
        self.assertNotIn(V163_FINAL,new)
        self.assertEqual(new.count("V164_SC_Y1_NESTED irq="),1)
        self.assertIn("addr==0x805293f8u&&ctx.lr==0x80526c98u",CONTINUE)
        self.assertIn("return; // execute original guest scheduler-disable function",CONTINUE)
        self.assertIn("addr==INT_DISABLE||addr==INT_RESTORE",OBSERVER)
        self.assertIn("ctx.lr>=0x805293f8u",OBSERVER)
        self.assertIn("ctx.lr<0x80529434u",OBSERVER)
        self.assertIn("ctx.inst_count>v164_start_inst",OBSERVER)
        self.assertIn("ctx.gpr[13]==v147_first_r13",OBSERVER)
        self.assertIn("Mail::Y1",OBSERVER)
        self.assertIn("Irq::IPC_PPC",OBSERVER)
        self.assertIn("queued_replies()==0u",OBSERVER)
        self.assertIn("IOS::Device::File",OBSERVER)

    def test_first_irq_observers_not_removed_only_limited_to_first_phase(self):
        before=previous(self.base)
        after=derive(self.base)
        for old,new in ((OLD_NESTED,SCOPED_NESTED),
                        (OLD_REGISTERED,SCOPED_REGISTERED),
                        (OLD_V144,SCOPED_V144)):
            self.assertEqual(before.count(old),1,old[:65])
            self.assertEqual(after.count(new),1,new[:65])
            self.assertNotIn(old,after)
            self.assertIn("v161_dispatch_seen==0u",new)
        for marker in ("++v144_disable_seen;", "++v145_ipc_seen;", "++v143_time_seen;"):
            self.assertEqual(before.count(marker),after.count(marker),marker)

    def test_no_guest_cpu_mutations_or_new_ios_steps(self):
        old=previous(self.base)
        new=derive(self.base)
        for token in ("ctx.mmu.write8(", "ctx.mmu.write16(", "ctx.mmu.write32(",
                      "ipc70_ram.write8(", "ipc70_bus.write32(", "ipc70_bus.tick(",
                      "scheduler.service_one(ctx.msr)", "enter_external_irq("):
            self.assertEqual(old.count(token),new.count(token),token)
        for pattern in (r"ctx\.gpr\[[^\]]+\]\s*=(?!=)",
                        r"ctx\.msr\s*=(?!=)", r"ctx\.srr0\s*=(?!=)",
                        r"ctx\.srr1\s*=(?!=)"):
            self.assertEqual(len(re.findall(pattern,old)),
                             len(re.findall(pattern,new)),pattern)

    def test_sixteen_owner_trials_and_secure_cleanup(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for marker in ("derive_v164_sc_y1_nested_helper_harness.py",
                       "V161_SC_Y1_DISPATCH verified=1",
                       "V162_SC_REPLY_NEXT verified=1",
                       "V163_SC_Y1_DISABLE verified=1",
                       "V164_SC_Y1_NESTED verified=1",
                       'test "$(grep -Ec'):
            self.assertIn(marker,script)
        example=("V164_SC_Y1_NESTED irq=1 reply=1 masked=1 guest=1 "
                 "caller=1 target=1 pc=805265ac lr=8052940c")
        self.assertTrue(re.fullmatch(PASS,example))
        self.assertFalse(re.fullmatch(PASS,example.replace("reply=1","reply=0")))
        self.assertFalse(re.fullmatch(PASS,example.replace("target=1","target=0")))
        with tempfile.TemporaryDirectory() as td:
            file=Path(td)/"runner.sh";file.write_text(script,encoding="utf-8")
            subprocess.run(["bash","-n",str(file)],check=True)
        with self.assertRaises(ValueError):derive("invalid")
        with self.assertRaises(ValueError):runner("invalid")
        wf=(HERE.parents[1]/".github/workflows/wii-v164-sc-y1-nested-helper.yml").read_text(encoding="utf-8")
        self.assertIn("run_v164_sc_y1_nested_helper.sh",wf)
        self.assertIn("V164_SC_Y1_NESTED verified=1",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)

if __name__=="__main__":
    unittest.main()
