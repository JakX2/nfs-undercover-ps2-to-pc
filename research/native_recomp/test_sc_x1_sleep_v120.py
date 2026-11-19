#!/usr/bin/env python3
"""Original-free V120 X1 IPC control write and sleep entry validation."""
from pathlib import Path
import subprocess
import tempfile
import unittest
from derive_v119_sc_control_write_harness import derive as previous
from derive_v120_sc_x1_sleep_harness import EDITS,derive
from derive_v120_sc_x1_sleep_runner import derive as runner

HERE=Path(__file__).resolve().parent

class V120(unittest.TestCase):
    def test_harness(self):
        base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        old=previous(base)
        actual=derive(base)
        expected=old
        for before,after in EDITS:
            self.assertEqual(expected.count(before),1,before[:100])
            expected=expected.replace(before,after,1)
        self.assertEqual(actual,expected)
        self.assertEqual(actual,derive(base))
        for marker in ("POST_OWNER=0x8052a430u",
                       "if(post119_control==1u&&addr==POST_OWNER&&ctx.lr==0x805197d8u)",
                       "V120_X1_SLEEP_ENTRY route=",
                       "post118_msg==1u&&post118_x1==1u",
                       "(*ctrl&M::X1)!=0u",
                       "post120_sleep==1u&&nwii::runtime::post119_control==1u"):
            self.assertIn(marker,actual)
        for marker in ("ctx.mmu.write","seed_stm_data(","ipc70_bus.reset()"):
            self.assertEqual(actual.count(marker),old.count(marker))

    def test_runner(self):
        src=(HERE/"run_v79_continuous_reply_entry.sh").read_text(encoding="utf-8")
        actual=runner(src)
        for marker in ("BOOT_PROGRESS entry=0x8000403C pc=0x8052A430 stage=120",
                       "V120_X1_SLEEP_ENTRY route=1 sent=1 wire=1 abi=1 prior=1",
                       "V120_NATIVE_EXIT ok=1"):
            self.assertIn(marker,actual)
        with tempfile.TemporaryDirectory() as td:
            file=Path(td)/"run.sh"
            file.write_text(actual,encoding="utf-8")
            subprocess.run(["bash","-n",str(file)],check=True)

    def test_workflow(self):
        wf=(HERE.parents[1]/".github/workflows/wii-v120-sc-x1-sleep.yml").read_text(encoding="utf-8")
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        for f in ("run_v120_continuous_sc_x1_sleep.sh",
                  "diagnose_sc_x1_sleep_v120.py"):
            self.assertTrue((HERE/f).is_file(),f)
            self.assertIn(f,wf)
        for marker in ("'.github/workflows/wii-v120-sc-x1-sleep.yml'",
                       "V120_X1_SLEEP_ENTRY route=1 sent=1 wire=1 abi=1 prior=1",
                       "BOOT_PROGRESS entry=0x8000403C pc=0x8052A430 stage=120",
                       "WII_ORIGINAL_DOL_ID","WII_ORIGINAL_ELF_ID",
                       "V119_CTRL_WRITE_ENTRY route=1 reads=1 wire=1 abi=1 prior=1"):
            self.assertIn(marker,wf)

if __name__=="__main__":
    unittest.main()
