#!/usr/bin/env python3
"""V236 original-free Wii IOS_OpenAsync caller-sequence correlation tests."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v235_sc_isfs_helper_abi_harness import derive as previous, NEXT_EXTRA as PREVIOUS_EXTRA
from derive_v236_sc_second_ios_callers_harness import derive, TRACE, SEND, NEXT_EXTRA
from derive_v236_sc_second_ios_callers_runner import derive as runner, ENTRY, PATTERN, PASS
HERE=Path(__file__).resolve().parent
class V236(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        src=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=previous(src);cls.after=derive(src)
    def test_genuine_ios_caller_sequence(self):
        for x in ("addr==0x8051982cu",
                  "v183_second_phys==0u",
                  "v236_ios_count<8u","ctx.lr==0x804f1eccu",
                  "v153_phys!=0u","v236_late_count",
                  "V236_IOS","lr="):
            self.assertIn(x,TRACE)
        for x in ("read32(value+12u)","read32(value+16u)",
                  "v236_last_path","v236_last_mode",
                  "V236_SUBMIT","++v236_submit_seen"):
            self.assertIn(x,SEND)
        self.assertIn(NEXT_EXTRA,self.after)
        self.assertIn(PREVIOUS_EXTRA,self.after)
        with self.assertRaises(ValueError):derive("unmatched source")
    def test_never_force_guest_arguments_or_ios_state(self):
        for x in ("scheduler.service_one(","ipc70_bus.write32(",
                  "ctx.mmu.write32(","ipc70_ram.write8("):
            self.assertEqual(self.before.count(x),self.after.count(x))
        for x in (TRACE,SEND):
            for bad in ("ctx.mmu.write","ipc70_bus.write","ipc70_ram.write",
                        "<<pathname<<","<<v236_last_path<<","<<v236_last_mode<<"):
                self.assertNotIn(bad,x)
            self.assertNotRegex(x,r"ctx\.gpr\[[0-9]+\]\s*=(?!=)")
    def test_exact_16_owner_trials_and_cleanup(self):
        s=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for x in ("derive_v236_sc_second_ios_callers_harness.py",
                  "V235_SC_ISFS_HELPER_ABI verified=1",
                  "V236_SC_SECOND_IOS_CALLERS verified=1"):
            self.assertIn(x,s)
        entry="V236_IOS seq=2 after_first=1 from_isfs=0 lr_isfs=0 lr_text=1 path=0 sysconf=0 modevalid=0 mode_mem2=1 cb=1 lr=8051982c"
        self.assertIsNotNone(re.fullmatch(ENTRY,entry))
        summ="V236_SUBMIT entries=2 early=1 late=1 isfs=1 after_first=1 from_isfs=0 pathvalid=0 modevalid=0 same_path=1 same_mode=1 original_caller=1 lr=8051982c"
        self.assertIsNotNone(re.fullmatch(PASS,summ))
        self.assertIsNone(re.fullmatch(PASS,summ.replace("same_mode=1","same_mode=0")))
        wf=(HERE.parents[1]/".github/workflows/wii-v236-sc-second-ios-callers.yml").read_text()
        for x in ("run_v236_sc_second_ios_callers.sh",
                  "test_v236_sc_second_ios_callers.py",
                  "V236_SC_SECOND_IOS_CALLERS verified=1"):
            self.assertIn(x,wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)
        with tempfile.TemporaryDirectory() as tmp:
            for name,data in (("runner",s),("wrapper",(HERE/"run_v236_sc_second_ios_callers.sh").read_text())):
                p=Path(tmp)/name;p.write_text(data,encoding="utf-8")
                subprocess.run(["bash","-n",str(p)],check=True)
if __name__=="__main__":
    unittest.main()
