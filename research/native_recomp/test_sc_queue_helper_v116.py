#!/usr/bin/env python3
"""V116 native IOS interrupt-disable and queue-helper source-only regression guards."""
from pathlib import Path
import subprocess
import tempfile
import unittest
from derive_v115_sc_irq_disable_harness import derive as previous
from derive_v116_sc_queue_helper_harness import EDITS,derive
from derive_v116_sc_queue_helper_runner import derive as runner

HERE=Path(__file__).resolve().parent

class V116(unittest.TestCase):
    def test_owner_harness_derived_exactly(self):
        base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        old=previous(base)
        got=derive(base)
        expected=old
        for before,after in EDITS:
            self.assertEqual(expected.count(before),1,before[:90])
            expected=expected.replace(before,after,1)
        self.assertEqual(got,expected)
        self.assertEqual(got,derive(base))
        for marker in ("POST_OWNER=0x8051afe0u",
                       "if(post115_sc==1u&&addr==INT_DISABLE&&ctx.lr==0x80519640u)",
                       "V116_QUEUE_HELPER route=",
                       "post116_queue==1u&&nwii::runtime::post115_disable==1u",
                       "!(ctx.msr&0x8000u)&&ctx.gpr[1]<post98_root_stack"):
            self.assertIn(marker,got)
        self.assertNotIn("stop before executing original IRQ-disable function",got)
        for marker in ("ctx.mmu.write","seed_stm_data(","ipc70_bus.reset()"):
            self.assertEqual(got.count(marker),old.count(marker))

    def test_runner_well_formed(self):
        result=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text(encoding="utf-8"))
        for marker in ("BOOT_PROGRESS entry=0x8000403C pc=0x8051AFE0 stage=116",
                       "V116_QUEUE_HELPER route=1 pointer=1 abi=1 prior=1",
                       "V116_NATIVE_EXIT ok=1",
                       "V115_VECTOR_ENTRY valid=1"):
            self.assertIn(marker,result)
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"runner.sh";p.write_text(result,encoding="utf-8")
            subprocess.run(["bash","-n",str(p)],check=True)

    def test_workflow_integrity(self):
        s=(HERE.parents[1]/".github/workflows/wii-v116-sc-queue-helper.yml").read_text(encoding="utf-8")
        for filename in ("run_v116_continuous_sc_queue_helper.sh",
                         "diagnose_sc_queue_helper_v116.py"):
            self.assertTrue((HERE/filename).is_file(),filename)
            self.assertIn(filename,s)
        for marker in ("V115_DISABLE_ENTRY route=1 abi=1 prior=1",
                       "V116_QUEUE_HELPER route=1 pointer=1 abi=1 prior=1",
                       "BOOT_PROGRESS entry=0x8000403C pc=0x8051AFE0 stage=116",
                       "WII_ORIGINAL_DOL_ID","WII_ORIGINAL_ELF_ID",
                       "'.github/workflows/wii-v116-sc-queue-helper.yml'"):
            self.assertIn(marker,s)
        self.assertIn("for attempt in 1 2 3; do",s)
        self.assertIn("staged != 1",s)
        self.assertIn("stage_owner_wii_gdown.py",s)
        self.assertNotIn("run_v115_continuous_sc_async_submit.sh",s)

if __name__=="__main__":
    unittest.main()
