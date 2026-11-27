#!/usr/bin/env python3
"""Exact owner-128 native aggregate and eight-trial contract, original-free."""
import unittest
from validate_formatter_nested_log import mixed_markers, verify

ARGS = dict(
    caller_report_branch_128=True, integer_count=2, post_integer_count=1,
    mixed_integers=2, mixed_taken=2, mixed_fallthrough=1,
)

class Original128BranchLog(unittest.TestCase):
    def records(self):
        tag, trial, total = mixed_markers(2,1,2,2,1,branch_128=True)
        self.assertEqual(tag,'FORMATTER_CALLER_REPORT_BRANCH_128')
        self.assertIn('total_visits=1024',total)
        self.assertIn('branches_128_verified=8 branch_taken=8',total)
        return [trial.pattern.replace('([0-7])',str(i)) for i in range(8)],total

    def test_exact_native_128_owner_census(self):
        trials,total=self.records()
        self.assertEqual(verify(trials+[total],**ARGS),(total,))

    def test_fail_closed_missing_swapped_or_repeated_trial(self):
        trials,total=self.records()
        self.assertRaises(ValueError,verify,trials[:7]+[total],**ARGS)
        self.assertRaises(ValueError,verify,trials+trials[-1:]+[total],**ARGS)
        self.assertRaises(ValueError,verify,[trials[1]]+trials[1:]+[total],**ARGS)

    def test_refuse_forged_execution_and_misattributed_127(self):
        trials,total=self.records()
        for bad in (
            total.replace('total_visits=1024','total_visits=1016'),
            total.replace('fallback=0','fallback=1'),
            total.replace('branches_128_verified=8','branches_128_verified=0'),
            total.replace('branch_taken=8','branch_taken=0'),
            total.replace('branch_taken=8','branch_taken=9'),
            total.replace('original_execution','synthetic_execution'),
            total.replace('FORMATTER_CALLER_REPORT_BRANCH_128_NATIVE',
                          'FORMATTER_CALLER_REPORT_SIXTH_IMMEDIATE_NATIVE'),
        ):
            with self.subTest(bad=bad[:65]):
                self.assertRaises(ValueError,verify,trials+[bad],**ARGS)
        self.assertRaises(ValueError,verify,trials+[total,
                          'FORMATTER_128_REFUSAL kind=1'],**ARGS)

if __name__=='__main__':
    unittest.main(verbosity=2)
