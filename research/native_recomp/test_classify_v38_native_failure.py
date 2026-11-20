#!/usr/bin/env python3
"""Synthetic safety regressions for V38 private assertion classification."""
import unittest
from classify_v38_native_failure import classify

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

    def test_four_digit_public_assertion_catalog(self):
        # Entirely synthetic, deterministic source strings; no owner data.
        source="".join(f'check(true,"public-only-{i:05d}");\n' for i in range(1050))
        result=classify(source,"  what(): public-only-01049\n")
        self.assertEqual(result,1050)
        self.assertEqual(classify(source,"  what(): private-guess-01049\n"),0)

    def test_catalog_above_four_digit_bound_fails_closed(self):
        source="".join(f'check(true,"public-only-{i:05d}");\n' for i in range(10001))
        with self.assertRaisesRegex(ValueError,"4-digit"):
            classify(source,"  what(): public-only-10000\n")

    def test_public_source_has_deterministic_identifier(self):
        self.assertNotEqual(classify(PUBLIC,"  what(): first source-only assertion\n"),
                            classify(PUBLIC,"  what(): second source-only assertion\n"))


if __name__=="__main__":
    unittest.main()
