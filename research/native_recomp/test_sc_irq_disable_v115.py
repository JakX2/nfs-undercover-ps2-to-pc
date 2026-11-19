#!/usr/bin/env python3
"""V115 original-free authentic syscall-vector and IRQ-disable boundary tests."""
from pathlib import Path
import subprocess
import tempfile
import unittest
from derive_v114_sc_flush_syscall_harness import derive as previous
from derive_v115_sc_irq_disable_harness import EDITS,derive
from derive_v115_sc_irq_disable_runner import derive as runner

HERE=Path(__file__).resolve().parent

class V115(unittest.TestCase):
    def test_harness_derivation(self):
        src=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        old=previous(src)
        actual=derive(src)
        expected=old
        for before,after in EDITS:
            self.assertEqual(expected.count(before),1,before[:100])
            expected=expected.replace(before,after,1)
        self.assertEqual(actual,expected)
        self.assertEqual(actual,derive(src))
        for marker in ("POST_OWNER=0x805265acu",
                       "V115_VECTOR_ENTRY valid=",
                       "V115_DISABLE_ENTRY route=",
                       "ctx.srr0==0x805222ecu",
                       "native_idle_cache_sc(ctx,SYSCALL_DEST",
                       "post115_disable==1u&&nwii::runtime::post115_sc==1u"):
            self.assertIn(marker,actual)
        self.assertNotIn("stop before authentic syscall vector, never synthesize completion",actual)
        for marker in ("ctx.mmu.write","seed_stm_data(","ipc70_bus.reset()"):
            self.assertEqual(actual.count(marker),old.count(marker))

    def test_runner_derivation(self):
        src=(HERE/"run_v79_continuous_reply_entry.sh").read_text(encoding="utf-8")
        result=runner(src)
        for marker in ("BOOT_PROGRESS entry=0x8000403C pc=0x805265AC stage=115",
                       "V115_VECTOR_ENTRY valid=1",
                       "V115_DISABLE_ENTRY route=1 abi=1 prior=1",
                       "V115_NATIVE_EXIT ok=1"):
            self.assertIn(marker,result)
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/"run.sh"
            out.write_text(result,encoding="utf-8")
            subprocess.run(["bash","-n",str(out)],check=True)

    def test_workflow_privacy_and_provenance(self):
        p=HERE.parents[1]/".github/workflows/wii-v115-sc-irq-disable.yml"
        self.assertTrue(p.is_file())
        s=p.read_text(encoding="utf-8")
        for f in ("run_v115_continuous_sc_irq_disable.sh",
                  "diagnose_sc_irq_disable_v115.py"):
            self.assertTrue((HERE/f).is_file(),f)
            self.assertIn(f,s)
        for marker in (".github/workflows/wii-v115-sc-irq-disable.yml",
                       "V114_CACHE_SYSCALL route=1 flushed=1 abi=1 prior=1",
                       "V115_VECTOR_ENTRY valid=1",
                       "V115_DISABLE_ENTRY route=1 abi=1 prior=1",
                       "BOOT_PROGRESS entry=0x8000403C pc=0x805265AC stage=115",
                       "WII_ORIGINAL_DOL_ID","WII_ORIGINAL_ELF_ID"):
            self.assertIn(marker,s)
        self.assertNotIn("run_v115_continuous_sc_async_submit.sh",s)

if __name__=="__main__":
    unittest.main()
