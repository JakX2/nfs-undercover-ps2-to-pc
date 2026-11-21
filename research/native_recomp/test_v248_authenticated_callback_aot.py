#!/usr/bin/env python3
"""V248 synthetic-only AOT regeneration and owner-private stage tests."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v248_authenticated_callback_aot_runner import derive as runner, PATTERN, PASS, BUILD
from derive_v247_private_callback_restore_runner import derive as parent
HERE=Path(__file__).resolve().parent

class V248(unittest.TestCase):
    def test_inherits_owner_proof_and_regenerates_in_private_temp(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for marker in ("V247_SC_PRIVATE_CALLBACK_RESTORE verified=1",
                       "V248_SC_AUTH_AOT verified=1",
                       "V248_REGEN generator=1",
                       "V248_REGEN scan=1",
                       '"$work/v247-restored.dol"',
                       '"$work/v248-generated/output.cpp"',
                       '"$work/v248-scan.log")" -eq 1'):
            self.assertIn(marker,script)
        self.assertEqual(script.count("V248_SC_AUTH_AOT verified=1"),1)
        self.assertEqual(script.count("V247_SC_PRIVATE_CALLBACK_RESTORE verified=1"),1)
        self.assertNotIn("upload-artifact",script)
        self.assertNotIn("ctx.pc=0x",BUILD)
        self.assertNotIn("ctx.gpr[",BUILD)
        self.assertNotIn("source.cpp",BUILD)
        self.assertIn('> "$work/v248-generator.log" 2>&1',BUILD)
        self.assertIn('> "$work/v248-scan.log" 2>&1',BUILD)
        self.assertIn("V245_AOT_DIAG stage=",BUILD)
        with tempfile.TemporaryDirectory() as tmp:
            for filename,content in (("derived.sh",script),
                    ("wrapper.sh",(HERE/"run_v248_authenticated_callback_aot.sh").read_text())):
                p=Path(tmp)/filename;p.write_text(content,encoding="utf-8")
                subprocess.run(["bash","-n",str(p)],check=True)

    def test_bounded_authenticated_aot_output(self):
        good=("V245_AOT_MAP owner=1 fixture_cb=1 fixture_isfs=1 fixture_nand=1 fixture_ipc=1 "
              "cb_entry=1 cb_prologue=1 cb_bctrl=1 cb_link=1 cb_ctr=1 cb_return=1 "
              "isfs_entry=1 isfs_prologue=1 isfs_save=1 nand_entry=1 "
              "dispatch_cb=1 dispatch_isfs=1 dispatch_nand=1")
        self.assertIsNotNone(re.fullmatch(PASS,good))
        self.assertIsNotNone(re.fullmatch(PATTERN,good.replace("cb_ctr=1","cb_ctr=0")))
        self.assertIsNone(re.fullmatch(PASS,good.replace("cb_link=1","cb_link=0")))
        self.assertIsNone(re.fullmatch(PATTERN,good+" code=secret"))
        wf=(HERE.parents[1]/".github/workflows/wii-v248-authenticated-callback-aot.yml").read_text()
        for marker in ("run_v248_authenticated_callback_aot.sh",
                       "test_v248_authenticated_callback_aot.py",
                       "V248_SC_AUTH_AOT verified=1"):
            self.assertIn(marker,wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)

if __name__=="__main__":
    unittest.main()
