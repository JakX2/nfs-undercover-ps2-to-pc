#!/usr/bin/env python3
"""V118 original-free tests for independent second IOS request PPCMSG/X1 handling."""
from pathlib import Path
import subprocess
import tempfile
import unittest
from derive_v117_sc_send_register_harness import derive as previous
from derive_v118_sc_async_mailbox_harness import EDITS,derive
from derive_v118_sc_async_mailbox_runner import derive as runner

HERE=Path(__file__).resolve().parent

class V118(unittest.TestCase):
    def test_harness_derives_exactly(self):
        src=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        before=previous(src);result=derive(src);current=before
        for a,b in EDITS:
            self.assertEqual(current.count(a),1,a[:90])
            current=current.replace(a,b,1)
        self.assertEqual(result,current)
        self.assertEqual(result,derive(src))
        for marker in ("POST_OWNER=0x8052a430u",
                       "V118_PPCMSG wire=","V118_PPCCTRL route=",
                       "V118_SLEEP_ENTRY route=","V118_WALK seq=",
                       "post118_sleep==1u&&nwii::runtime::post118_msg==1u",
                       "ipc70_bus.write32(addr,value)"):
            self.assertIn(marker,result)
        for marker in ("seed_stm_data(","ipc70_bus.reset()"):
            self.assertEqual(result.count(marker),before.count(marker))
        self.assertEqual(result.count("ctx.mmu.write"),before.count("ctx.mmu.write"))
        self.assertIn("post118_msg==1u&&post118_x1==0u",result)

    def test_runner_is_valid(self):
        s=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text(encoding="utf-8"))
        for marker in ("V118_PPCMSG wire=1 path=1",
                       "V118_PPCCTRL route=1 request=1",
                       "V118_SLEEP_ENTRY route=1 wire=1 abi=1 prior=1",
                       "BOOT_PROGRESS entry=0x8000403C pc=0x8052A430 stage=118"):
            self.assertIn(marker,s)
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"runner.sh";path.write_text(s,encoding="utf-8")
            subprocess.run(["bash","-n",str(path)],check=True)

    def test_privacy_and_pinning(self):
        wf=(HERE.parents[1]/".github/workflows/wii-v118-sc-async-mailbox.yml").read_text(encoding="utf-8")
        for filename in ("run_v118_continuous_sc_async_mailbox.sh",
                         "diagnose_sc_async_mailbox_v118.py"):
            self.assertIn(filename,wf)
            self.assertTrue((HERE/filename).is_file())
        for marker in ("V118_PPCMSG wire=1 path=1","V118_PPCCTRL route=1 request=1",
                       "V118_SLEEP_ENTRY route=1 wire=1 abi=1 prior=1",
                       "BOOT_PROGRESS entry=0x8000403C pc=0x8052A430 stage=118",
                       "WII_ORIGINAL_DOL_ID","WII_ORIGINAL_ELF_ID",
                       "for attempt in 1 2 3; do",
                       "'.github/workflows/wii-v118-sc-async-mailbox.yml'"):
            self.assertIn(marker,wf)

if __name__=="__main__":
    unittest.main()
