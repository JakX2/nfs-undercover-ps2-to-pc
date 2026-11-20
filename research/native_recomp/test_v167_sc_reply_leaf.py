#!/usr/bin/env python3
"""Original-free V167 SC reply handler first guest leaf and Y1 invariants."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v166_sc_post_restore_harness import derive as previous
from derive_v167_sc_reply_leaf_harness import (
    derive, STATE, RESET, STOP, CONTINUE, OBSERVER,
    TRACE_ANCHOR, V166_FINAL, V167_FINAL, V166_CHECK, V167_CHECK,
    V166_TRIAL_END, V167_TRIAL_END, V166_LAST, V167_LAST,
    PREVIOUS_TRIAL, NEXT_TRIAL,
)
from derive_v167_sc_reply_leaf_runner import derive as runner, PASS

HERE=Path(__file__).resolve().parent

class V167(unittest.TestCase):
    def setUp(self):
        self.base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")

    def test_original_ipc_handler_and_prior_native_gates_preserved(self):
        old=previous(self.base)
        new=derive(self.base)
        for key in (STATE,RESET,STOP,TRACE_ANCHOR,V166_FINAL,
                    V166_CHECK,V166_TRIAL_END,PREVIOUS_TRIAL):
            self.assertEqual(old.count(key),1,key[:75])
        self.assertEqual(PREVIOUS_TRIAL.count(V166_LAST),1)
        self.assertNotIn(STOP,new)
        self.assertIn(CONTINUE,new)
        self.assertIn(OBSERVER,new)
        self.assertIn(NEXT_TRIAL,new)
        self.assertEqual(new.count(V167_FINAL),1)
        self.assertEqual(new.count(V167_CHECK),1)
        self.assertEqual(new.count(V167_TRIAL_END),1)
        self.assertEqual(new.count(V167_LAST),1)
        self.assertNotIn(V166_FINAL,new)
        self.assertNotIn(V166_CHECK,new)
        self.assertIn("addr==0x80519318u&&ctx.lr==0x80526cacu",CONTINUE)
        self.assertIn("return; // run original Y1 IPC interrupt handler guest code",CONTINUE)
        self.assertIn("ctx.inst_count>v167_start_inst",OBSERVER)
        self.assertIn("ctx.lr>=0x80519318u&&ctx.lr<0x805194c4u",OBSERVER)
        self.assertIn("v167_target_pc=addr;v167_target_lr=ctx.lr",OBSERVER)
        self.assertIn("IOS::Device::File",OBSERVER)
        self.assertIn("queued_replies()==0u",OBSERVER)
        self.assertIn("Mail::Y1",OBSERVER)
        self.assertIn("Irq::IPC_PPC",OBSERVER)
        self.assertEqual(new.count("V167_SC_REPLY_LEAF y1="),1)

    def test_no_guest_cpu_ios_or_irq_fabrication(self):
        old=previous(self.base)
        new=derive(self.base)
        for key in ("ctx.mmu.write8(", "ctx.mmu.write16(", "ctx.mmu.write32(",
                    "ipc70_ram.write8(", "ipc70_bus.write32(",
                    "scheduler.service_one(ctx.msr)", "ipc70_bus.tick(",
                    "enter_external_irq("):
            self.assertEqual(old.count(key),new.count(key),key)
        for reg in (r"ctx\.gpr\[[^\]]+\]\s*=(?!=)",r"ctx\.msr\s*=(?!=)",
                    r"ctx\.srr0\s*=(?!=)",r"ctx\.srr1\s*=(?!=)"):
            self.assertEqual(len(re.findall(reg,old)),len(re.findall(reg,new)),reg)

    def test_runner_sixteen_and_cleanup(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for key in ("derive_v167_sc_reply_leaf_harness.py",
                    "V164_SC_Y1_NESTED verified=1",
                    "V165_SC_POST_OSDI verified=1",
                    "V166_SC_POST_RESTORE verified=1",
                    "V167_SC_REPLY_LEAF verified=1",
                    'test "$(grep -Ec'):
            self.assertIn(key,script)
        example=("V167_SC_REPLY_LEAF y1=1 reply=1 guest=1 masked=1 "
                 "caller=1 read=1 pc=8051905c lr=8051935c")
        self.assertTrue(re.fullmatch(PASS,example))
        self.assertFalse(re.fullmatch(PASS,example.replace("y1=1","y1=0")))
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/"script.sh";p.write_text(script,encoding="utf-8")
            subprocess.run(["bash","-n",str(p)],check=True)
        with self.assertRaises(ValueError):derive("invalid")
        with self.assertRaises(ValueError):runner("invalid")
        workflow=(HERE.parents[1]/".github/workflows/wii-v167-sc-reply-leaf.yml").read_text(encoding="utf-8")
        self.assertIn("run_v167_sc_reply_leaf.sh",workflow)
        self.assertIn("V167_SC_REPLY_LEAF verified=1",workflow)
        self.assertEqual(workflow.count("      - name: Remove private owner and generated code"),1)

if __name__=="__main__":
    unittest.main()
