#!/usr/bin/env python3
"""V119 original-free IPC control read and write-helper boundary regressions."""
from pathlib import Path
import subprocess
import tempfile
import unittest
from derive_v118_sc_async_mailbox_harness import derive as previous
from derive_v119_sc_control_write_harness import EDITS,derive
from derive_v119_sc_control_write_runner import derive as runner
HERE=Path(__file__).resolve().parent

class V119(unittest.TestCase):
    def test_harness(self):
        base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        earlier=previous(base)
        result=derive(base)
        expected=earlier
        for old,new in EDITS:
            self.assertEqual(expected.count(old),1,old[:100])
            expected=expected.replace(old,new,1)
        self.assertEqual(result,expected)
        self.assertEqual(result,derive(base))
        for marker in ("POST_OWNER=0x8051906cu",
                       "if(post117_send==1u&&addr==0x8051905cu&&ctx.lr==0x805197b8u)",
                       "if(post118_sleep==1u&&post117_send==1u&&addr==POST_OWNER&&ctx.lr==0x805197c8u)",
                       "V119_CTRL_WRITE_ENTRY route=",
                       "post118_reads>0u&&post118_reads<=64u",
                       "post119_control==1u&&nwii::runtime::post118_sleep==1u"):
            self.assertIn(marker,result)
        for marker in ("ctx.mmu.write","seed_stm_data(","ipc70_bus.reset()"):
            self.assertEqual(result.count(marker),earlier.count(marker))

    def test_runner(self):
        source=(HERE/"run_v79_continuous_reply_entry.sh").read_text(encoding="utf-8")
        result=runner(source)
        for marker in ("BOOT_PROGRESS entry=0x8000403C pc=0x8051906C stage=119",
                       "V119_CTRL_WRITE_ENTRY route=1 reads=1 wire=1 abi=1 prior=1",
                       "V119_NATIVE_EXIT ok=1"):
            self.assertIn(marker,result)
        with tempfile.TemporaryDirectory() as td:
            file=Path(td)/"run.sh"
            file.write_text(result,encoding="utf-8")
            subprocess.run(["bash","-n",str(file)],check=True)

    def test_workflow(self):
        wf=(HERE.parents[1]/".github/workflows/wii-v119-sc-control-write.yml").read_text(encoding="utf-8")
        for name in ("run_v119_continuous_sc_control_write.sh",
                     "diagnose_sc_control_write_v119.py"):
            self.assertTrue((HERE/name).is_file(),name)
            self.assertIn(name,wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertEqual(wf.count("grep -E '^V118_CTRL_READ_ENTRY route=1 abi=1 prior=1 msg=[01]$'"),1)
        self.assertIn("V119_CTRL_WRITE_ENTRY route=1 reads=1 wire=1 abi=1 prior=1",wf)
        self.assertNotIn("\n\n      - name: Remove private owner and generated code",wf)
        for marker in ("'.github/workflows/wii-v119-sc-control-write.yml'",
                       "V119_CTRL_WRITE_ENTRY route=1 reads=1 wire=1 abi=1 prior=1",
                       "BOOT_PROGRESS entry=0x8000403C pc=0x8051906C stage=119",
                       "WII_ORIGINAL_DOL_ID","WII_ORIGINAL_ELF_ID"):
            self.assertIn(marker,wf)

if __name__=="__main__":
    unittest.main()
