#!/usr/bin/env python3
"""V118 source-only regression: observed IPC read boundary, no fabricated submission."""
from pathlib import Path
import subprocess
import tempfile
import unittest
from derive_v117_sc_send_register_harness import derive as previous
from derive_v118_sc_async_mailbox_harness import EDITS,derive
from derive_v118_sc_async_mailbox_runner import derive as runner

HERE=Path(__file__).resolve().parent

class V118(unittest.TestCase):
    def test_harness(self):
        source=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        old=previous(source)
        actual=derive(source)
        expected=old
        for before,after in EDITS:
            self.assertEqual(expected.count(before),1,before[:95])
            expected=expected.replace(before,after,1)
        self.assertEqual(actual,expected)
        self.assertEqual(actual,derive(source))
        for marker in ("POST_OWNER=0x8051905cu",
                       "if(post117_send==1u&&addr==POST_OWNER&&ctx.lr==0x805197b8u)",
                       "V118_CTRL_READ_ENTRY route=",
                       "post118_sleep==1u&&nwii::runtime::post117_send==1u",
                       "V118_WALK seq="):
            self.assertIn(marker,actual)
        self.assertNotIn("if(addr==POST_OWNER&&ctx.lr==0x805197b8u){",actual)
        # The same original helper is entered during an earlier synchronous request.
        # The V118 stop must be armed only after V117's async transport entry.
        self.assertEqual(actual.count("if(post117_send==1u&&addr==POST_OWNER&&ctx.lr==0x805197b8u)"),1)
        for marker in ("ctx.mmu.write","seed_stm_data(","ipc70_bus.reset()"):
            self.assertEqual(actual.count(marker),old.count(marker))
    def test_runner(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text(encoding="utf-8"))
        self.assertIn("BOOT_PROGRESS entry=0x8000403C pc=0x8051905C stage=118",script)
        self.assertIn("V118_CTRL_READ_ENTRY route=1 abi=1 prior=1 msg=[01]",script)
        self.assertIn('grep -E \'^V118_CTRL_READ_ENTRY route=[01]',script)
        self.assertIn('"$work/private-native.log" | sort -u || true',script)
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"run.sh"
            path.write_text(script,encoding="utf-8")
            subprocess.run(["bash","-n",str(path)],check=True)
    def test_private_ci(self):
        wf=(HERE.parents[1]/".github/workflows/wii-v118-sc-async-mailbox.yml").read_text(encoding="utf-8")
        for file in ("run_v118_continuous_sc_async_mailbox.sh",
                     "diagnose_sc_async_mailbox_v118.py"):
            self.assertTrue((HERE/file).is_file())
            self.assertIn(file,wf)
        for marker in ("V118_CTRL_READ_ENTRY route=1 abi=1 prior=1 msg=[01]",
                       "BOOT_PROGRESS entry=0x8000403C pc=0x8051905C stage=118",
                       "WII_ORIGINAL_DOL_ID","WII_ORIGINAL_ELF_ID",
                       "for attempt in 1 2 3; do",
                       "'.github/workflows/wii-v118-sc-async-mailbox.yml'"):
            self.assertIn(marker,wf)

if __name__=="__main__":
    unittest.main()
