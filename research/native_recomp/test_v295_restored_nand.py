#!/usr/bin/env python3
"""V295 original-free process outcome and inheritance guards."""
import unittest
from analyze_v295_restored_native import classify
from derive_v295_restored_nand_runner import patch, DONE

SAMPLE = (
    "V250_CB_BEGIN candidate=1 reply=1 captured=1\n"
    "V289_NAND_ENTRY n=1 phase=0 zero=1 sc=1 guest=1 inst=887\n"
)

class Tests(unittest.TestCase):
    def test_success_and_return_diagnostics(self):
        s, safe = classify(SAMPLE, 0)
        self.assertTrue(safe)
        self.assertIn("class=exit_zero rc=0", s)
        self.assertIn("nand_entries=1", s)
        s, safe = classify(SAMPLE, 1)
        self.assertTrue(safe)
        self.assertIn("completed=0", s)

    def test_timeout_and_failure_are_not_boot_success(self):
        s, safe = classify(SAMPLE, 124)
        self.assertTrue(safe)
        self.assertIn("class=timeout", s)
        self.assertIn("completed=0", s)
        s, safe = classify(SAMPLE, 139)
        self.assertTrue(safe)
        self.assertIn("class=signal", s)
        self.assertIn("completed=0", s)
        s, safe = classify(SAMPLE, 126)
        self.assertFalse(safe)
        self.assertIn("class=launch_failure", s)

    def test_no_guest_or_silent_candidate_fails(self):
        self.assertFalse(classify("", 0)[1])
        self.assertFalse(classify(SAMPLE.replace("guest=1", "guest=0"), 0)[1])
        self.assertFalse(classify(SAMPLE.replace("V250_CB_BEGIN", "X_CB_BEGIN"), 0)[1])
        with self.assertRaisesRegex(ValueError, "invalid_exit_code"):
            classify(SAMPLE, -11)
        with self.assertRaisesRegex(ValueError, "oversized_output"):
            classify("x" * 8_000_001, 0)

    def test_runner_is_separate_and_bounded(self):
        candidate = patch(DONE + "\nV294_AOT_STAGE link=1\n")
        self.assertIn("kill-after=3s 30s", candidate)
        self.assertIn("owner-callback", candidate)
        self.assertIn("analyze_v295_restored_native.py", candidate)
        with self.assertRaises(ValueError):
            patch("no V294 linker")

if __name__ == "__main__":
    unittest.main()
