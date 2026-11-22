#!/usr/bin/env python3
"""V308 synthetic-only symbol-window / interior-call tests."""
import unittest
from resolve_v308_descendant_boundaries import Window, resolve

BASE=0x80545100
class Tests(unittest.TestCase):
    def test_exact_entry(self):
        self.assertEqual(resolve({BASE:128},BASE),Window("exact",BASE,0,128))

    def test_branch_to_function_interior(self):
        self.assertEqual(
            resolve({BASE:128},BASE+4),
            Window("interior",BASE,4,124)
        )

    def test_unknown_callee_never_given_invented_length(self):
        self.assertEqual(
            resolve({BASE:128},BASE+128),
            Window("unknown",0,0,0)
        )

    def test_ambiguous_containing_functions_are_not_guessed(self):
        self.assertEqual(
            resolve({BASE:128,BASE+8:64},BASE+16),
            Window("ambiguous",0,0,0)
        )

    def test_invalid_exact_size_does_not_borrow_parent(self):
        self.assertEqual(
            resolve({BASE:128,BASE+4:3},BASE+4),
            Window("invalid",0,0,0)
        )

    def test_zero_or_unaligned_target_fails(self):
        for target in (0,BASE+1):
            with self.subTest(target=target):
                with self.assertRaisesRegex(ValueError,"invalid_target"):
                    resolve({BASE:128},target)

if __name__=="__main__":
    unittest.main()
