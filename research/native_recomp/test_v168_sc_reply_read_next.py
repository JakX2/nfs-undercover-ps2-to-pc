#!/usr/bin/env python3
"""Original-free V168 Y1 IPC read helper and second guest call regression."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from derive_v167_sc_reply_leaf_harness import derive as previous
from derive_v168_sc_reply_read_next_harness import (
    derive, STATE, RESET, STOP, CONTINUE, OBSERVATION, TRACE_ANCHOR,
    V167_FINAL, V168_FINAL, V167_CHECK, V168_CHECK,
    V167_TRIAL_END, V168_TRIAL_END, V167_LAST, V168_LAST,
    PREVIOUS_TRIAL, NEXT_TRIAL,
)
from derive_v168_sc_reply_read_next_runner import derive as runner, PASS

HERE=Path(__file__).resolve().parent

class V168(unittest.TestCase):
    def setUp(self):
        self.base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")

    def test_execute_only_authenticated_original_y1_ipc_read(self):
        old=previous(self.base)
        new=derive(self.base)
        for needle in (STATE,RESET,STOP,TRACE_ANCHOR,V167_FINAL,
                       V167_CHECK,V167_TRIAL_END,PREVIOUS_TRIAL):
            self.assertEqual(old.count(needle),1,needle[:74])
        self.assertEqual(PREVIOUS_TRIAL.count(V167_LAST),1)
        self.assertNotIn(STOP,new)
        self.assertIn(CONTINUE,new)
        self.assertIn(OBSERVATION,new)
        self.assertIn(NEXT_TRIAL,new)
        self.assertEqual(new.count(V168_FINAL),1)
        self.assertEqual(new.count(V168_CHECK),1)
        self.assertEqual(new.count(V168_TRIAL_END),1)
        self.assertEqual(new.count(V168_LAST),1)
        self.assertNotIn(V167_FINAL,new)
        self.assertNotIn(V167_CHECK,new)
        self.assertIn("addr==0x8051905cu&&ctx.lr==0x8051933cu",CONTINUE)
        self.assertIn("return; // run original Wii IPC register-read guest instructions",CONTINUE)
        self.assertIn("ctx.inst_count>v168_start_inst",OBSERVATION)
        self.assertIn("ctx.gpr[13]==v147_first_r13",OBSERVATION)
        self.assertIn("ctx.lr>=0x80519318u&&ctx.lr<0x805194c4u",OBSERVATION)
        self.assertIn("const bool other=addr!=v167_target_pc||ctx.lr!=v167_target_lr",OBSERVATION)
        self.assertIn("IOS::Device::File",OBSERVATION)
        self.assertIn("queued_replies()==0u",OBSERVATION)
        self.assertIn("Mail::Y1",OBSERVATION)
        self.assertIn("Irq::IPC_PPC",OBSERVATION)
        self.assertEqual(new.count("V168_SC_REPLY_NEXT y1="),1)

    def test_no_forged_guest_cpu_or_ios_acknowledgement(self):
        old=previous(self.base)
        new=derive(self.base)
        for token in ("ctx.mmu.write8(", "ctx.mmu.write16(", "ctx.mmu.write32(",
                      "ipc70_ram.write8(", "ipc70_bus.write32(",
                      "scheduler.service_one(ctx.msr)", "ipc70_bus.tick(",
                      "enter_external_irq("):
            self.assertEqual(old.count(token),new.count(token),token)
        for pattern in (r"ctx\.gpr\[[^\]]+\]\s*=(?!=)",r"ctx\.msr\s*=(?!=)",
                        r"ctx\.srr0\s*=(?!=)",r"ctx\.srr1\s*=(?!=)"):
            self.assertEqual(len(re.findall(pattern,old)),
                             len(re.findall(pattern,new)),pattern)

    def test_original_runner_16_trials_and_private_cleanup(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for token in ("derive_v168_sc_reply_read_next_harness.py",
                      "V166_SC_POST_RESTORE verified=1",
                      "V167_SC_REPLY_LEAF verified=1",
                      "V168_SC_REPLY_NEXT verified=1",
                      'test "$(grep -Ec'):
            self.assertIn(token,script)
        good=("V168_SC_REPLY_NEXT y1=1 reply=1 guest=1 masked=1 "
              "caller=1 read=1 other=1 pc=8051905c lr=8051935c")
        self.assertTrue(re.fullmatch(PASS,good))
        self.assertFalse(re.fullmatch(PASS,good.replace("other=1","other=0")))
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/"script.sh"
            p.write_text(script,encoding="utf-8")
            subprocess.run(["bash","-n",str(p)],check=True)
        with self.assertRaises(ValueError):derive("invalid")
        with self.assertRaises(ValueError):runner("invalid")
        workflow=(HERE.parents[1]/".github/workflows/wii-v168-sc-reply-read-next.yml").read_text(encoding="utf-8")
        self.assertIn("run_v168_sc_reply_read_next.sh",workflow)
        self.assertIn("V168_SC_REPLY_NEXT verified=1",workflow)
        self.assertEqual(workflow.count("      - name: Remove private owner and generated code"),1)

if __name__=="__main__":
    unittest.main()
