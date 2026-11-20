#!/usr/bin/env python3
"""Original-free V162 second-IRQ guest-call and inherited phase-scope safety."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v161_sc_y1_dispatch_harness import derive as previous
from derive_v162_sc_reply_next_harness import (
    derive, STATE, RESET, STOP, CONTINUE, OBSERVATION, TRACE_ANCHOR,
    OLDER_V76, SCOPED_V76, OLDER_V143, SCOPED_V143,
    PREVIOUS_TRIAL, NEXT_TRIAL, V161_PC, V162_PC,
    V161_FINAL_PC, V162_FINAL_PC, V161_NEXT_PC,
)
from derive_v162_sc_reply_next_runner import derive as runner, PASS

HERE=Path(__file__).resolve().parent

class V162(unittest.TestCase):
    def setUp(self):
        self.base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")

    def test_release_only_second_irq_dispatcher(self):
        prior=previous(self.base)
        new=derive(self.base)
        for anchor in (STATE,RESET,STOP,OLDER_V76,OLDER_V143,
                       TRACE_ANCHOR,PREVIOUS_TRIAL,V161_PC):
            self.assertEqual(prior.count(anchor),1,anchor[:80])
        self.assertNotIn(STOP,new)
        self.assertIn(CONTINUE,new)
        self.assertIn(OBSERVATION,new)
        self.assertIn(NEXT_TRIAL,new)
        self.assertIn(V162_PC,new)
        self.assertIn(V162_FINAL_PC,new)
        self.assertEqual(prior.count(V161_FINAL_PC),1)
        self.assertEqual(prior.count(V161_NEXT_PC),1)
        self.assertEqual(new.count(V162_FINAL_PC),2)
        self.assertNotIn(V161_FINAL_PC,new)
        self.assertNotIn(V161_NEXT_PC,new)
        self.assertEqual(new.count("V162_SC_REPLY_NEXT irq="),1)
        self.assertIn("ctx.inst_count>v162_dispatch_inst",OBSERVATION)
        self.assertIn("ctx.gpr[13]==v147_first_r13",OBSERVATION)
        self.assertIn("ipc70_bus.services().queued_replies()==0u",OBSERVATION)
        self.assertIn("IOS::Device::File",OBSERVATION)
        self.assertIn("Mail::Y1",OBSERVATION)
        self.assertIn("Irq::IPC_PPC",OBSERVATION)
        self.assertIn("ctx.lr>=0x80526a3cu&&ctx.lr<0x80526ce0u",OBSERVATION)

    def test_earlier_irq_observers_remain_live_in_first_phase_only(self):
        old=previous(self.base)
        new=derive(self.base)
        self.assertIn(SCOPED_V76,new)
        self.assertIn(SCOPED_V143,new)
        self.assertNotIn(OLDER_V76,new)
        self.assertNotIn(OLDER_V143,new)
        self.assertIn("irq76_dispatch&&v161_dispatch_seen==0u",SCOPED_V76)
        self.assertIn("v161_dispatch_seen==0u",SCOPED_V143)
        self.assertEqual(old.count("++irq76_time;"),new.count("++irq76_time;"))
        self.assertEqual(old.count("++v143_time_seen;"),new.count("++v143_time_seen;"))

    def test_no_guest_register_or_ios_device_state_mutation(self):
        before=previous(self.base)
        after=derive(self.base)
        for token in ("ctx.mmu.write8(", "ctx.mmu.write16(", "ctx.mmu.write32(",
                      "ipc70_ram.write8(", "ipc70_bus.write32(", "ipc70_bus.tick(",
                      "scheduler.service_one(ctx.msr)", "enter_external_irq("):
            self.assertEqual(before.count(token),after.count(token),token)
        for regex in (r"ctx\.gpr\[[^\]]+\]\s*=(?!=)",
                      r"ctx\.msr\s*=(?!=)",r"ctx\.srr0\s*=(?!=)",r"ctx\.srr1\s*=(?!=)"):
            self.assertEqual(len(re.findall(regex,before)),len(re.findall(regex,after)),regex)

    def test_owner_runner_and_cleanup(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for marker in ("derive_v162_sc_reply_next_harness.py",
                       "V160_SC_VECTOR_HANDLER verified=1",
                       "V161_SC_Y1_DISPATCH verified=1",
                       "V162_SC_REPLY_NEXT verified=1",
                       'test "$(grep -Ec'):
            self.assertIn(marker,script)
        good=("V162_SC_REPLY_NEXT irq=1 reply=1 guest=1 masked=1 caller=1 "
              "pc=8052a824 lr=80526c84")
        self.assertTrue(re.fullmatch(PASS,good))
        self.assertFalse(re.fullmatch(PASS,good.replace("irq=1","irq=0")))
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/"runner.sh";p.write_text(script,encoding="utf-8")
            subprocess.run(["bash","-n",str(p)],check=True)
        with self.assertRaises(ValueError):derive("invalid")
        with self.assertRaises(ValueError):runner("invalid")
        wf=(HERE.parents[1]/".github/workflows/wii-v162-sc-reply-next.yml").read_text(encoding="utf-8")
        self.assertIn("run_v162_sc_reply_next.sh",wf)
        self.assertIn("V162_SC_REPLY_NEXT verified=1",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)

if __name__=="__main__":
    unittest.main()
