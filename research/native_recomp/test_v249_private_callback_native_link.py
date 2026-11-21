#!/usr/bin/env python3
"""V249 original-free restored AOT candidate compile/link checks."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v245_sc_aot_map_runner import derive as previous
from derive_v249_private_callback_native_link_runner import (
    derive, DONE, ROW, SCAN, STAGE,
)

HERE=Path(__file__).resolve().parent

class V249(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old=(HERE/"run_v79_continuous_reply_entry.sh").read_text(encoding="utf-8")
        cls.before=previous(cls.old)
        cls.after=derive(cls.old)

    def test_restore_and_candidate_compilation(self):
        self.assertEqual(self.before.count(DONE),1)
        self.assertIn(DONE,self.after)
        for part in (
            'test -s "$work/private-v248.dol"',
            'test -s "$work/generated-v248/output.cpp"',
            'test -s "$work/generated/output.cpp"',
            '"$work/v248-restore.log"',
            '"$work/v248-aot.log"',
            'cmp -s "$work/generated/output.cpp" "$work/generated-v248/output.cpp"',
            'g++ -std=c++20 -O2',
            '-Werror -Wno-type-limits -Wno-unused-label',
            '-c "$work/generated-v248/output.cpp" -o "$work/v249-generated.o"',
            'g++ "$work/harness.o" "$work/v249-generated.o" "$work/loader.o"',
            '-o "$work/v249-native"',
            "V249_SC_AUTH_CALLBACK_LINK verified=1",
        ):
            self.assertIn(part,self.after)
        self.assertEqual(self.after.count("echo 'V249_AOT_LINK owner=1"),1)
        self.assertIsNotNone(re.fullmatch(ROW,
            "V249_AOT_LINK owner=1 restore=1 mapping=1 different=1 compiled=1 linked=1 executable=1"))
        self.assertIsNotNone(re.fullmatch(SCAN,
            "V245_AOT_MAP owner=1 fixture_cb=1 fixture_isfs=1 fixture_nand=1 fixture_ipc=1 cb_entry=1 cb_prologue=1 cb_bctrl=1 cb_link=1 cb_ctr=1 cb_return=1 isfs_entry=1 isfs_prologue=1 isfs_save=1 nand_entry=1 dispatch_cb=1 dispatch_isfs=1 dispatch_nand=1"))
        with self.assertRaises(ValueError):derive("no original runner checkpoint")

    def test_no_private_source_disclosure_or_guest_execution(self):
        for forbidden in ("cat $work","cat \"$work","sed -n", "objdump",
                          "cp \"$work/generated","upload-artifact",
                          '"$work/v249-native" "$work/private',
                          "ctx.pc=", "ctx.gpr[", "ipc70_ram.write"):
            self.assertNotIn(forbidden,STAGE)
        for expected in (
            "V249_AOT_DIAG stage=compare kind=identical",
            "V249_AOT_DIAG stage=compile kind=failed",
            "V249_AOT_DIAG stage=link kind=failed",
            "V249_AOT_LINK owner=1"):
            self.assertIn(expected,STAGE)
        self.assertNotIn("V249_SC_AUTH_CALLBACK_LINK verified=1",self.before)

    def test_runner_and_workflow_fail_closed(self):
        workflow=(HERE.parents[1]/".github/workflows/wii-v249-private-callback-native-link.yml").read_text()
        for m in ("run_v249_private_callback_native_link.sh",
                  "test_v249_private_callback_native_link.py",
                  "V249_SC_AUTH_CALLBACK_LINK verified=1"):
            self.assertIn(m,workflow)
        self.assertEqual(workflow.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",workflow)
        with tempfile.TemporaryDirectory() as tmp:
            for name,content in (("runner.sh",self.after),
                                 ("wrapper.sh",(HERE/"run_v249_private_callback_native_link.sh").read_text())):
                path=Path(tmp)/name
                path.write_text(content,encoding="utf-8")
                subprocess.run(["bash","-n",str(path)],check=True)

if __name__=="__main__":
    unittest.main()
