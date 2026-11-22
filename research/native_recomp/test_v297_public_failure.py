#!/usr/bin/env python3
"""V297 original-free service PC progression and public-only label tests."""
import unittest
from analyze_v297_public_failure import analyze
from derive_v297_public_failure_runner import patch, DONE

PUBLIC='static void check(bool, const char*); check(false, "A public harness failure");'
LOG=(
    "V250_CB_BEGIN candidate=1 reply=1 captured=1\n"
    "V289_NAND_ENTRY n=1 phase=0 zero=1 sc=1 guest=1 inst=100\n"
    "V296_SERVICE_ENTRY kind=1 guest=1 direct=1 inst=124\n"
    "what(): A public harness failure\n"
)

class Tests(unittest.TestCase):
    def test_public_assertion_and_execution_delta(self):
        summary,label,valid=analyze(LOG,PUBLIC,134)
        self.assertTrue(valid)
        self.assertIn("delta=24 ordered=1 abort=1",summary)
        self.assertIn("label=A public harness failure",label)

    def test_missing_or_inconsistent_progress_fails(self):
        self.assertFalse(analyze(LOG.replace("inst=124","inst=99"),PUBLIC,134)[2])
        self.assertFalse(analyze(LOG.replace("kind=1","kind=2"),PUBLIC,134)[2])
        self.assertFalse(analyze(LOG.replace("A public harness failure\n",
                                              "A private unknown error\n"),PUBLIC,134)[2])
        with self.assertRaises(ValueError):
            analyze(LOG,PUBLIC,-1)

    def test_inherited_runner_is_original_only(self):
        text=patch(DONE+"\npython3 analyze_v296_native_frontier.py")
        self.assertIn("analyze_v297_public_failure.py",text)
        self.assertIn("v296-harness.cpp",text)
        with self.assertRaises(ValueError):
            patch("not the V296 native runner")

if __name__=="__main__":
    unittest.main()
