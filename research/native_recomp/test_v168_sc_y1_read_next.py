#!/usr/bin/env python3
"""Original-free V168 proof that actual Y1 reply IPC read advances to next BL."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v167_sc_reply_leaf_harness import derive as previous
from derive_v168_sc_y1_read_next_harness import (
    derive, STATE, RESET, STOP, CONTINUE, OBSERVATION, TRACE_ANCHOR,
    PREVIOUS_TRIAL, NEXT_TRIAL, V167_FINAL, V168_FINAL,
    V167_CHECK, V168_CHECK, V167_TRIAL_END, V168_TRIAL_END,
    V167_LAST, V168_LAST,
)
from derive_v168_sc_y1_read_next_runner import derive as runner, PASS

HERE=Path(__file__).resolve().parent

class V168(unittest.TestCase):
    def setUp(self):
        self.base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")

    def test_releases_only_authenticated_original_reply_read(self):
        old=previous(self.base)
        new=derive(self.base)
        for key in (STATE,RESET,STOP,TRACE_ANCHOR,PREVIOUS_TRIAL,
                    V167_FINAL,V167_CHECK,V167_TRIAL_END):
            self.assertEqual(old.count(key),1,key[:72])
        self.assertEqual(PREVIOUS_TRIAL.count(V167_LAST),1)
        self.assertNotIn(STOP,new)
        self.assertIn(CONTINUE,new)
        self.assertIn(OBSERVATION,new)
        self.assertIn(NEXT_TRIAL,new)
        for key in (V168_FINAL,V168_CHECK,V168_TRIAL_END,V168_LAST):
            self.assertEqual(new.count(key),1,key[:72])
        for key in (V167_FINAL,V167_CHECK,V167_TRIAL_END,V167_LAST):
            self.assertNotIn(key,new)
        self.assertIn("addr==0x8051905cu&&ctx.lr==0x8051933cu",CONTINUE)
        self.assertIn("return; // execute the original PPC control-read helper",CONTINUE)
        self.assertIn("v168_target_pc=addr;v168_target_lr=ctx.lr",OBSERVATION)
        self.assertIn("ctx.inst_count>v168_start_inst",OBSERVATION)
        self.assertIn("ctx.gpr[13]==v147_first_r13",OBSERVATION)
        self.assertIn("ctx.lr>=0x80519318u&&ctx.lr<0x805194c4u",OBSERVATION)
        self.assertIn("Mail::Y1",OBSERVATION)
        self.assertIn("Mail::ARMMSG",OBSERVATION)
        self.assertIn("queued_replies()==0u",OBSERVATION)
        self.assertIn("IOS::Device::File",OBSERVATION)
        self.assertIn("Irq::IPC_PPC",OBSERVATION)
        self.assertIn("read=",OBSERVATION)
        self.assertIn("write=",OBSERVATION)
        self.assertEqual(new.count("V168_SC_REPLY_NEXT y1="),1)

    def test_does_not_forge_reply_or_guest_state(self):
        old=previous(self.base)
        new=derive(self.base)
        for token in ("ctx.mmu.write8(", "ctx.mmu.write16(", "ctx.mmu.write32(",
                      "ipc70_ram.write8(", "ipc70_bus.write32(", "ipc70_bus.tick(",
                      "scheduler.service_one(ctx.msr)", "enter_external_irq("):
            self.assertEqual(old.count(token),new.count(token),token)
        for regex in (r"ctx\.gpr\[[^\]]+\]\s*=(?!=)",
                      r"ctx\.msr\s*=(?!=)", r"ctx\.srr0\s*=(?!=)",
                      r"ctx\.srr1\s*=(?!=)"):
            self.assertEqual(len(re.findall(regex,old)),len(re.findall(regex,new)),regex)

    def test_owner_runner_sixteen_and_rejects_missing_y1(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for token in ("derive_v168_sc_y1_read_next_harness.py",
                      "V166_SC_POST_RESTORE verified=1",
                      "V167_SC_REPLY_LEAF verified=1",
                      "V168_SC_REPLY_NEXT verified=1",
                      'test "$(grep -Ec'):
            self.assertIn(token,script)
        good=("V168_SC_REPLY_NEXT y1=1 reply=1 guest=1 masked=1 caller=1 "
              "read=1 write=0 pc=8051905c lr=80519358")
        self.assertTrue(re.fullmatch(PASS,good))
        self.assertFalse(re.fullmatch(PASS,good.replace("y1=1","y1=0")))
        self.assertFalse(re.fullmatch(PASS,good.replace("reply=1","reply=0")))
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/"run.sh"
            p.write_text(script,encoding="utf-8")
            subprocess.run(["bash","-n",str(p)],check=True)

    def test_fail_closed_and_private_cleanup(self):
        with self.assertRaises(ValueError):derive("invalid")
        with self.assertRaises(ValueError):runner("invalid")
        workflow=(HERE.parents[1]/".github/workflows/wii-v168-sc-y1-read-next.yml").read_text(encoding="utf-8")
        self.assertIn("run_v168_sc_y1_read_next.sh",workflow)
        self.assertIn("V168_SC_REPLY_NEXT verified=1",workflow)
        self.assertEqual(workflow.count("      - name: Remove private owner and generated code"),1)

if __name__=="__main__":
    unittest.main()
