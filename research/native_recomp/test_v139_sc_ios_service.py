#!/usr/bin/env python3
"""Source-owned V139 Wii IOS SC request service regression checks."""
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v138_ios_request_harness import derive as previous
from derive_v139_sc_ios_service_harness import derive,ANCHOR,ADDITION
from derive_v139_sc_ios_service_runner import derive as derive_runner
HERE=Path(__file__).resolve().parent

class V139(unittest.TestCase):
    def test_original_guest_execution_is_not_patched(self):
        src=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text()
        old=previous(src)
        self.assertEqual(old.count(ANCHOR),1)
        new=derive(src)
        self.assertIn('undercover::wii::SysconfImage::add_to(*v139_files)',new)
        self.assertIn('v139_scheduler.service_one(ctx.msr)',new)
        self.assertIn("V139_SC_IOS_ACK mount=",new)
        self.assertIn("v138_kind==4u&&v138_mode==1u",new)
        self.assertEqual(new.count(ADDITION),1)
        for name in ("ctx.mmu.write8(","ctx.mmu.write32(",
                     "ipc70_ram.write8(","ctx.gpr[3]=",
                     "ctx.cr[0].eq="):
            self.assertEqual(old.count(name),new.count(name))
        self.assertEqual(new.count("#include \"wii_sysconf_image.h\""),1)
        self.assertEqual(new.count("#include \"wii_ios_yield_scheduler.h\""),1)

    def test_runner_requires_every_native_trial(self):
        src=(HERE/"run_v79_continuous_reply_entry.sh").read_text()
        runner=derive_runner(src)
        for string in ("derive_v139_sc_ios_service_harness.py",
                       "V136_SECOND_RETRY verified=1",
                       "V137_IOS_PROBE verified=1",
                       "V138_REQUEST_PROBE verified=1",
                       "V139_SC_ACK verified=1"):
            self.assertIn(string,runner)
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"run.sh";p.write_text(runner)
            subprocess.run(["bash","-n",str(p)],check=True)

    def test_changed_original_free_anchors_fail_closed(self):
        with self.assertRaises(ValueError):derive("other")
        with self.assertRaises(ValueError):derive_runner("other")

if __name__=="__main__":unittest.main()
