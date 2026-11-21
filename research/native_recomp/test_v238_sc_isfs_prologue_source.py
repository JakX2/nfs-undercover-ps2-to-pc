#!/usr/bin/env python3
"""V238 public original-free second ISFS prologue provenance tests."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v237_sc_isfs_reentry_harness import derive as previous, NEXT_EXTRA as PREVIOUS_EXTRA
from derive_v238_sc_isfs_prologue_source_harness import derive, TRACE, SEND, NEXT_EXTRA
from derive_v238_sc_isfs_prologue_source_runner import derive as runner, ENTRY, PATTERN, PASS
HERE=Path(__file__).resolve().parent
class V238(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        src=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=previous(src);cls.after=derive(src)
    def test_original_prologue_saved_lr_and_args(self):
        for token in ("addr==0x80545100u&&ctx.lr==0x804f1e40u",
              "ctx.mmu.get_ptr(sp+36u)",
              "ctx.mmu.read32(sp+36u)",
              "caller==0x8051de3cu","caller==0x8051f700u",
              "ctx.gpr[11]==sp+32u","ctx.gpr[4]<=3u",
              "V238_SAVE","++v238_save_count"):
            self.assertIn(token,TRACE)
        for token in ("V238_SOURCE","v236_last_mode",
                      "v238_second_mode","++v238_source_seen"):
            self.assertIn(token,SEND)
        self.assertIn(NEXT_EXTRA,self.after)
        self.assertIn(PREVIOUS_EXTRA,self.after)
        with self.assertRaises(ValueError):derive("unknown source")
    def test_no_proprietary_data_or_guest_write(self):
        for marker in ("scheduler.service_one(","ipc70_bus.write32(",
                     "ctx.mmu.write32(","ipc70_ram.write8("):
            self.assertEqual(self.before.count(marker),self.after.count(marker))
        for part in (TRACE,SEND):
            for bad in ("ctx.mmu.write","ipc70_bus.write","ipc70_ram.write",
                        "<<caller<<","<<pathptr<<","<<v238_second_mode<<"):
                self.assertNotIn(bad,part)
            self.assertNotRegex(part,r"ctx\.gpr\[[0-9]+\]\s*=(?!=)")
    def test_owner_16_trials_and_cleanup(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for marker in ("derive_v238_sc_isfs_prologue_source_harness.py",
              "V237_SC_ISFS_REENTRY verified=1",
              "V238_SC_ISFS_PROLOGUE verified=1"):
            self.assertIn(marker,script)
        example="V238_SAVE seq=2 mapped=1 nand=0 logging=1 other=0 r11=1 mode=0 srcmode=0 path=0 sysconf=0 nandcb=0"
        self.assertIsNotNone(re.fullmatch(ENTRY,example))
        good="V238_SOURCE saves=2 second=1 nand=0 logging=1 other=0 r11=1 modevalid=0 pathvalid=0 sysconf=0 same_ios_mode=1 ios_invalid=1"
        self.assertIsNotNone(re.fullmatch(PASS,good))
        self.assertIsNone(re.fullmatch(PASS,good.replace("ios_invalid=1","ios_invalid=0")))
        from diagnose_v238_compile_failure import diagnose
        sample="harness.cpp:8759:14: error: redeclaration of 'mapped'"
        self.assertEqual(diagnose(sample),
            "V238_COMPILE_DIAG found=1 kind=duplicate symbol=mapped line=8759")
        self.assertEqual(diagnose("confidential compiler message"),
            "V238_COMPILE_DIAG found=0 kind=none symbol=other line=0")
        self.assertIn("diagnose_v238_compile_failure.py",script)
        from diagnose_v238_compile_failure import explain_source
        source="void trace_call(){}\nconst bool mode = true;"
        self.assertEqual(explain_source(
            "harness.cpp:2:14: error: redeclaration of 'mode'",source),
            "V238_COMPILE_SOURCE public=1 v238=0 group=mode")
        self.assertEqual(explain_source("unknown",source),
            "V238_COMPILE_SOURCE public=0 v238=0 group=other")
        self.assertEqual(explain_source(
            "harness.cpp:2:14: error: redeclaration of 'v238_second_mode'",
            "static int x;\nstatic bool v238_second_mode=false;"),
            "V238_COMPILE_SOURCE public=1 v238=1 group=v238_state")

        wf=(HERE.parents[1]/".github/workflows/wii-v238-sc-isfs-prologue-source.yml").read_text()
        for marker in ("run_v238_sc_isfs_prologue_source.sh",
             "test_v238_sc_isfs_prologue_source.py","V238_SC_ISFS_PROLOGUE verified=1"):
            self.assertIn(marker,wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)
        with tempfile.TemporaryDirectory() as tmp:
            for name,src in (("runner",script),
                     ("wrapper",(HERE/"run_v238_sc_isfs_prologue_source.sh").read_text())):
                p=Path(tmp)/name;p.write_text(src,encoding="utf-8")
                subprocess.run(["bash","-n",str(p)],check=True)
if __name__=="__main__":
    unittest.main()
