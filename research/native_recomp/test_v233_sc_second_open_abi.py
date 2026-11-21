#!/usr/bin/env python3
"""V233 source-only original Wii upstream second IOS_Open ABI tests."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v214_sc_y2_negative_reply_harness import derive as previous, NEXT_END as PREVIOUS_END
from derive_v233_sc_second_open_abi_harness import derive, TRACE, SEND, NEXT_EXTRA
from derive_v233_sc_second_open_abi_runner import derive as runner, ABI, PATTERN
HERE=Path(__file__).resolve().parent
class V233(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        src=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=previous(src);cls.after=derive(src)
    def test_original_guest_wii_argument_vs_physical_request(self):
        for m in ("addr==0x804f1e2cu","addr==0x8051982cu","v153_phys!=0u",
                  "ctx.gpr[3]","ctx.gpr[4]","ctx.gpr[5]",
                  "ctx.mmu.get_ptr(p+i)","V233_ABI"):
            self.assertIn(m,TRACE)
        for m in ("read32(value+12u)","read32(value+16u)",
                  "v233_ios_path&0x3fffffffu","mode16==v233_ios_mode",
                  "V233_SUBMIT","++v233_send_seen"):
            self.assertIn(m,SEND)
        self.assertIn(NEXT_EXTRA,self.after)
        self.assertNotIn(PREVIOUS_END,self.after)
        with self.assertRaises(ValueError):derive("unmatched source")
    def test_privacy_and_no_guest_mutation(self):
        for marker in ("scheduler.service_one(","ipc70_ram.write8(",
                       "ctx.mmu.write32(","ipc70_bus.write32("):
            self.assertEqual(self.before.count(marker),self.after.count(marker))
        for part in (TRACE,SEND):
            for banned in ("ctx.gpr[3]=","ctx.gpr[4]=","ctx.mmu.write",
                           "ipc70_ram.write","ipc70_bus.write",
                           "<<path12","<<mode16","<<v233_ios_path"):
                self.assertNotIn(banned,part)
    def test_bounded_owner_trials_and_cleanup(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for m in ("derive_v233_sc_second_open_abi_harness.py",
                  "V214_SC_Y2_NEGATIVE verified=1",
                  "V233_SC_SECOND_OPEN_ABI verified=1"):
            self.assertIn(m,script)
        self.assertIsNotNone(re.fullmatch(ABI,
            "V233_ABI layer=isfs path=1 sysconf=1 modevalid=1 callback=1 guest=1"))
        self.assertIsNotNone(re.fullmatch(PATTERN,
            "V233_SUBMIT isfs=1 ios=1 isfs_path12=0 isfs_mode16=0 "
            "ios_path12=0 ios_mode16=0 ios_shifted=1 isfs_cb=1 ios_cb=1"))
        wf=(HERE.parents[1]/".github/workflows/wii-v233-sc-second-open-abi.yml").read_text()
        for m in ("run_v233_sc_second_open_abi.sh",
                  "test_v233_sc_second_open_abi.py",
                  "V233_SC_SECOND_OPEN_ABI verified=1"):
            self.assertIn(m,wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)
        with tempfile.TemporaryDirectory() as tmp:
            for name,txt in (("runner",script),
                 ("wrapper",(HERE/"run_v233_sc_second_open_abi.sh").read_text())):
                p=Path(tmp)/name;p.write_text(txt,encoding="utf-8")
                subprocess.run(["bash","-n",str(p)],check=True)
if __name__=="__main__":
    unittest.main()
