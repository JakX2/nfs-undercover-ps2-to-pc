#!/usr/bin/env python3
"""V310 source-only restored descendant coverage acceptance tests."""
import unittest
from analyze_v310_restored_coverage import inspect

SUMMARY=(
    "V306_COVERAGE owner=1 targets=4 exact=2 interior=2 "
    "emitted=2 dispatch=2 missing=0 partial=0 unknown=0\n"
)
TARGET=(
    "V306_DESCENDANT pc=80519bcc kind=exact base=80519bcc offset=0 "
    "words=64 present=1 same=64 nop=0 blr=0 other=0 body=1 dispatch=1\n"
)
TWO=(
    "V306_DESCENDANT pc=80545104 kind=interior base=805450d0 offset=13 "
    "words=6 present=1 same=6 nop=0 blr=0 other=0 body=0 dispatch=0\n"
    "V306_DESCENDANT pc=80545150 kind=interior base=8054511c offset=13 "
    "words=6 present=1 same=6 nop=0 blr=0 other=0 body=0 dispatch=0\n"
)
class Tests(unittest.TestCase):
    def test_authenticated_restored_descendant_ready(self):
        report,valid=inspect(SUMMARY+TARGET+TWO)
        self.assertTrue(valid)
        self.assertIn("words=64 original=1 body=1 dispatch=1 interiors=1 ready=1",report)

    def test_nop_or_missing_native_edge_fails(self):
        for text in (
            (SUMMARY+TARGET+TWO).replace("same=64 nop=0","same=0 nop=64"),
            (SUMMARY+TARGET+TWO).replace("other=0 body=1","other=0 body=0"),
            (SUMMARY+TARGET+TWO).replace("dispatch=1\n","dispatch=0\n"),
            (SUMMARY+TARGET+TWO).replace("exact=2","exact=1"),
            (SUMMARY+TARGET+TWO).replace("partial=0","partial=1"),
            SUMMARY+TARGET+TWO.splitlines(keepends=True)[0]
        ):
            with self.subTest(text=text[:70]):
                result,valid=inspect(text)
                self.assertFalse(valid)
                self.assertIn("ready=0",result)

    def test_ambiguous_or_absent_source_rejected(self):
        with self.assertRaisesRegex(ValueError,"sanitized_rows"):
            inspect("")
        with self.assertRaisesRegex(ValueError,"sanitized_rows"):
            inspect(SUMMARY+TARGET+TWO+TARGET)

if __name__=="__main__":
    unittest.main()
