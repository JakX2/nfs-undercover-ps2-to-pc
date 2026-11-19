#!/usr/bin/env python3
"""V117 original-free queue helper and IPC register-write boundary regression tests."""
from pathlib import Path
import subprocess
import tempfile
import unittest
from derive_v116_sc_queue_helper_harness import derive as previous
from derive_v117_sc_send_register_harness import EDITS,derive
from derive_v117_sc_send_register_runner import derive as runner

HERE=Path(__file__).resolve().parent

class V117(unittest.TestCase):
    def test_harness(self):
        src=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        before=previous(src)
        got=derive(src)
        expected=before
        for old,new in EDITS:
            self.assertEqual(expected.count(old),1,old[:95])
            expected=expected.replace(old,new,1)
        self.assertEqual(got,expected)
        self.assertEqual(got,derive(src))
        for marker in ("POST_OWNER=0x8051906cu",
                       "if(post115_disable==1u&&addr==0x8051afe0u&&ctx.lr==0x805196d4u)",
                       "V117_SEND_REG route=",
                       "V117_WALK seq=",
                       "post117_send==1u&&nwii::runtime::post116_queue==1u"):
            self.assertIn(marker,got)
        for marker in ("ctx.mmu.write","seed_stm_data(","ipc70_bus.reset()"):
            self.assertEqual(got.count(marker),before.count(marker))

    def test_runner(self):
        src=(HERE/"run_v79_continuous_reply_entry.sh").read_text(encoding="utf-8")
        result=runner(src)
        for m in ("BOOT_PROGRESS entry=0x8000403C pc=0x8051906C stage=117",
                  "V117_SEND_REG route=1 abi=1 prior=1",
                  "V117_NATIVE_EXIT ok=1"):
            self.assertIn(m,result)
        with tempfile.TemporaryDirectory() as td:
            sh=Path(td)/"run.sh"
            sh.write_text(result,encoding="utf-8")
            subprocess.run(["bash","-n",str(sh)],check=True)

    def test_private_workflow(self):
        s=(HERE.parents[1]/".github/workflows/wii-v117-sc-send-register.yml").read_text(encoding="utf-8")
        for f in ("run_v117_continuous_sc_send_register.sh",
                  "diagnose_sc_send_register_v117.py"):
            self.assertTrue((HERE/f).is_file(),f)
            self.assertIn(f,s)
        for m in ("V116_QUEUE_HELPER route=1 pointer=1 abi=1 prior=1",
                  "V117_SEND_REG route=1 abi=1 prior=1",
                  "BOOT_PROGRESS entry=0x8000403C pc=0x8051906C stage=117",
                  "WII_ORIGINAL_DOL_ID","WII_ORIGINAL_ELF_ID",
                  "for attempt in 1 2 3; do",
                  "'.github/workflows/wii-v117-sc-send-register.yml'"):
            self.assertIn(m,s)

if __name__=="__main__":
    unittest.main()
