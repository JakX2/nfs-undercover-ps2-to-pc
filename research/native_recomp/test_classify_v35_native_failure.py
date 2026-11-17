#!/usr/bin/env python3
"""Synthetic safety regressions for V35 private assertion classification."""
import unittest
from classify_v35_native_failure import classify

PUBLIC = '''
#include <cstdio>
check(a,"first source-only assertion");
check(b,"second source-only assertion");
'''


class ClassifyTests(unittest.TestCase):
    def test_only_known_public_source_strings(self):
        n=classify(PUBLIC,"terminate called after throwing\n  what():  second source-only assertion\n")
        self.assertGreater(n,0)
        self.assertEqual(n,classify(PUBLIC,"  what():  second source-only assertion\n"))

    def test_unknown_private_details_redacted(self):
        self.assertEqual(classify(PUBLIC,"  what(): /private/original_wii/never-share.dol"),0)
        self.assertEqual(classify(PUBLIC,"random binary data \x00 \x02"),0)

    def test_public_source_has_deterministic_identifier(self):
        self.assertNotEqual(classify(PUBLIC,"  what(): first source-only assertion\n"),
                            classify(PUBLIC,"  what(): second source-only assertion\n"))


if __name__=="__main__":
    unittest.main()
