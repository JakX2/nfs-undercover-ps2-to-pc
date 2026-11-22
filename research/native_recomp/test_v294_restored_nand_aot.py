#!/usr/bin/env python3
"""V294 original-free AOT coverage, missing-entry and privacy tests."""
import unittest
from pathlib import Path
from analyze_v294_restored_aot import inspect,SIZES
from derive_v294_restored_nand_aot_runner import patch as patch_runner,DONE

def fixture(*,missing=None):
    rows=[
        "V292_AOT_REACH owner=1 fixture=1 targets=4 "
        "child_original=1 source_original=1 child_aot=1 "
        "source_aot=1 child_bl=1 unmapped_bl=0 direct_emit=1"
    ]
    for pc,size in SIZES.items():
        body=0 if pc==missing else 1
        rows.append(f"V292_AOT_TARGET pc={pc} words={size} "
                    f"present=1 same={size} nop=0 blr=0 other=0 "
                    f"emitted={body} dispatch={body}")
    return "\n".join(rows)

class Tests(unittest.TestCase):
    def test_full_private_aot_acceptance(self):
        row,ready=inspect(fixture())
        self.assertTrue(ready)
        self.assertIn("targets=4 exact=4 bodies=4 dispatch=4",row)
        self.assertIn("unmapped=0 direct_emit=1 ready=1",row)

    def test_missing_body_or_foreign_placeholder_fails(self):
        row,ready=inspect(fixture(missing="8051d20c"))
        self.assertFalse(ready)
        self.assertIn("bodies=3 dispatch=3",row)
        row,ready=inspect(fixture().replace(
            "pc=8052fca4 words=16 present=1 same=16 nop=0",
            "pc=8052fca4 words=16 present=1 same=15 nop=1"))
        self.assertFalse(ready)
        self.assertIn("exact=3",row)
        with self.assertRaisesRegex(ValueError,"audit_rows"):
            inspect("not a V292 SHA-verified audit")
        with self.assertRaisesRegex(ValueError,"audit_targets"):
            inspect(fixture().replace("pc=8051e150","pc=8051e151"))

    def test_runner_and_workflow_are_private(self):
        self.assertIn("analyze_v294_restored_aot.py",
                      patch_runner(DONE))
        with self.assertRaises(ValueError):
            patch_runner("not authenticated V293 runner")
        wf=(Path(__file__).resolve().parents[2]/
            ".github/workflows/wii-v294-restored-nand-aot.yml").read_text()
        self.assertIn("V294_COVERAGE_AUDIT verified=1",wf)
        self.assertIn("WII_ORIGINAL_ELF_ID",wf)
        self.assertNotIn("upload-artifact",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)

if __name__=="__main__":
    unittest.main()
