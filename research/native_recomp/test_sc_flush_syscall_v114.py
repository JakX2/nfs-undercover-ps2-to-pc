#!/usr/bin/env python3
"""Original-free V114 PowerPC cache-flush syscall boundary regressions."""
from pathlib import Path
import subprocess
import tempfile
import unittest
from derive_v113_sc_transport_queue_harness import derive as previous
from derive_v114_sc_flush_syscall_harness import EDITS,derive
from derive_v114_sc_flush_syscall_runner import derive as runner

HERE=Path(__file__).resolve().parent

class V114(unittest.TestCase):
    def test_harness_source_only(self):
        base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        old=previous(base)
        result=derive(base)
        current=old
        for before,after in EDITS:
            self.assertEqual(current.count(before),1,before[:100])
            current=current.replace(before,after,1)
        self.assertEqual(result,current)
        self.assertEqual(result,derive(base))
        self.assertEqual(result.count("POST_OWNER=0x805222e8u"),1)
        self.assertEqual(result.count("V114_CACHE_SYSCALL route="),1)
        self.assertIn("if(post112_submit==1u&&addr==0x805222c0u&&ctx.lr==0x8051963cu)",result)
        self.assertIn("post114_syscall==1u&&nwii::runtime::post113_flush==1u",result)
        self.assertIn("ctx.guest_flush_count==post114_before+lines",result)
        for marker in ("ctx.mmu.write","seed_stm_data(","ipc70_bus.reset()"):
            self.assertEqual(result.count(marker),old.count(marker))

    def test_runner_source_only(self):
        source=(HERE/"run_v79_continuous_reply_entry.sh").read_text(encoding="utf-8")
        s=runner(source)
        self.assertIn("BOOT_PROGRESS entry=0x8000403C pc=0x805222E8 stage=114",s)
        self.assertIn("V114_CACHE_SYSCALL route=1 flushed=1 abi=1 prior=1",s)
        self.assertIn("grep -Fx 'V114_CACHE_SYSCALL",s)
        with tempfile.TemporaryDirectory() as td:
            sh=Path(td)/"run.sh"
            sh.write_text(s,encoding="utf-8")
            subprocess.run(["bash","-n",str(sh)],check=True)

    def test_workflow_and_private_guards(self):
        path=HERE.parents[1]/".github/workflows/wii-v114-sc-flush-syscall.yml"
        self.assertTrue(path.is_file())
        wf=path.read_text(encoding="utf-8")
        for f in ("run_v114_continuous_sc_flush_syscall.sh",
                  "diagnose_sc_flush_syscall_v114.py"):
            self.assertTrue((HERE/f).is_file(),f)
            self.assertIn(f,wf)
        self.assertIn("'.github/workflows/wii-v114-sc-flush-syscall.yml'",wf)
        self.assertIn("V114_CACHE_SYSCALL route=1 flushed=1 abi=1 prior=1",wf)
        self.assertIn("BOOT_PROGRESS entry=0x8000403C pc=0x805222E8 stage=114",wf)
        self.assertIn("WII_ORIGINAL_DOL_ID",wf)
        self.assertIn("WII_ORIGINAL_ELF_ID",wf)
        self.assertNotIn("run_v113_continuous_sc_async_submit.sh",wf)

if __name__=="__main__":
    unittest.main()
