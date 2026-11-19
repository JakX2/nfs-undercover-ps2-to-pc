#!/usr/bin/env python3
"""Source-only V125 private fixture preflight safety and integration regressions."""
from pathlib import Path
import unittest
from verify_v125_owner_fixture import error_code,FAILURE_CODES
HERE=Path(__file__).resolve().parent

class V125OwnerFixture(unittest.TestCase):
    def test_fixed_error_vocabulary(self):
        self.assertEqual(len(FAILURE_CODES),len(set(FAILURE_CODES)))
        for index,message in enumerate(FAILURE_CODES,1):
            self.assertEqual(error_code(ValueError(message)),index)
        self.assertEqual(error_code(ValueError("SECRET_SENTINEL private owner text")),0)
    def test_private_bytes_not_published(self):
        source=(HERE/"verify_v125_owner_fixture.py").read_text()
        self.assertIn('print(f"V125_PREFLIGHT result=failed code=',source)
        self.assertNotIn("print(exc)",source)
        self.assertNotIn("traceback.print_exc",source)
        self.assertIn("verify(candidate, owner)",source)
        self.assertIn("inspect(candidate, owner.read_bytes())",source)
    def test_workflow_gating(self):
        wf=(HERE.parents[1]/".github/workflows/wii-v125-sc-helper.yml").read_text()
        self.assertEqual(wf.count("V125_PREFLIGHT result=verified"),0)
        self.assertEqual(wf.count("verify_v125_owner_fixture.py"),1)
        self.assertLess(wf.index("- name: Independently verify V125 private fixture restoration"),
                        wf.index("- name: Prepare pinned original-free NWii runtime"))
        source=(HERE.parents[1]/".github/workflows/native-recomp-source-checks.yml").read_text()
        self.assertIn("python3 research/native_recomp/test_v125_owner_fixture_source.py",source)
if __name__=="__main__":
    unittest.main()
