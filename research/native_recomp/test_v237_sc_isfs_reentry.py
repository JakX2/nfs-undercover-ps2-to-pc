#!/usr/bin/env python3
"""V237 original-free Wii ISFS prologue and IOS second entry frame tests."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v236_sc_second_ios_callers_harness import derive as previous, NEXT_EXTRA as PREVIOUS_EXTRA
from derive_v237_sc_isfs_reentry_harness import derive, TRACE, SEND, NEXT_EXTRA
from derive_v237_sc_isfs_reentry_runner import derive as runner, SECOND, PATTERN, PASS
HERE=Path(__file__).resolve().parent
class V237(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        src=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=previous(src);cls.after=derive(src)
    def test_guest_isfs_call_and_frame(self):
        for marker in ("addr==0x804f1e2cu","addr==0x80545100u&&ctx.lr==0x804f1e40u",
              "addr==0x80519094u&&ctx.lr==0x804f1e60u",
              "addr==0x8051ad38u&&ctx.lr==0x804f1e84u",
              "addr==0x80004338u&&ctx.lr==0x804f1eb4u",
              "addr==0x8051982cu&&ctx.lr==0x804f1eccu",
              "ctx.mmu.read32(ctx.gpr[1]+36u)",
              "ctx.gpr[27]==v237_source_mode","ctx.gpr[4]==ctx.gpr[27]",
              "V237_SECOND"):
            self.assertIn(marker,TRACE)
        self.assertIn("V237_CHAIN",SEND)
        self.assertIn(NEXT_EXTRA,self.after)
        self.assertIn(PREVIOUS_EXTRA,self.after)
        with self.assertRaises(ValueError):derive("not a valid public fixture")
    def test_read_only_bounded(self):
        for marker in ("scheduler.service_one(","ipc70_bus.write32(",
                      "ctx.mmu.write32(","ipc70_ram.write8("):
            self.assertEqual(self.before.count(marker),self.after.count(marker))
        for part in (TRACE,SEND):
            for bad in ("ctx.mmu.write","ipc70_bus.write","ipc70_ram.write",
                        "<<ctx.gpr","<<v237_first_sp<<","<<v237_first_lr<<"):
                self.assertNotIn(bad,part)
            self.assertNotRegex(part,r"ctx\.gpr\[[0-9]+\]\s*=(?!=)")
    def test_16_trials_and_cleanup(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for marker in ("derive_v237_sc_isfs_reentry_harness.py",
               "V236_SC_SECOND_IOS_CALLERS verified=1",
               "V237_SC_ISFS_REENTRY verified=1"):
            self.assertIn(marker,script)
        self.assertIsNotNone(re.fullmatch(SECOND,
          "V237_SECOND stack=1 saved_lr=1 r27valid=1 r27source=1 arg_r27=1 path_r30=1 same_r30=1"))
        sample="V237_CHAIN isfs=1 save=1 strn=1 alloc=1 copy=1 ios=2 stack=1 saved_lr=1 r27valid=1 r27source=1 arg_r27=1 path_r30=1"
        self.assertIsNotNone(re.fullmatch(PASS,sample))
        self.assertIsNone(re.fullmatch(PASS,sample.replace("ios=2","ios=1")))
        wf=(HERE.parents[1]/".github/workflows/wii-v237-sc-isfs-reentry.yml").read_text()
        for marker in ("run_v237_sc_isfs_reentry.sh",
               "test_v237_sc_isfs_reentry.py","V237_SC_ISFS_REENTRY verified=1"):
            self.assertIn(marker,wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)
        with tempfile.TemporaryDirectory() as tmp:
            for name,src in (("runner",script),("wrapper",(HERE/"run_v237_sc_isfs_reentry.sh").read_text())):
                p=Path(tmp)/name;p.write_text(src,encoding="utf-8")
                subprocess.run(["bash","-n",str(p)],check=True)
if __name__=="__main__":
    unittest.main()
