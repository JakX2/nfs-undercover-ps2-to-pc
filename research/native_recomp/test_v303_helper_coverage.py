#!/usr/bin/env python3
"""V303 original-free restored helper coverage acceptance and negatives."""
import unittest
from analyze_v303_helper_coverage import inspect, EXPECTED_WORDS

def row(*,same=41,nop=0,body=1,dispatch=1,caller=1,unmapped=0,direct=1):
    return (
      "V301_HELPER_AOT owner=1 elf=1 pc=804f2064 "
      f"words={EXPECTED_WORDS} present=1 same={same} nop={nop} "
      f"blr=0 other=0 body={body} dispatch={dispatch} "
      f"caller={caller} unmapped={unmapped} direct={direct}"
    )

class Tests(unittest.TestCase):
    def test_exact_authenticated_nand_helper(self):
        message,ready=inspect(row())
        self.assertTrue(ready)
        self.assertIn("original=1 words=41 body=1 dispatch=1",message)
        self.assertIn("unmapped=0 direct=1 ready=1",message)

    def test_untranslated_or_nop_body_fails(self):
        for data in (
            row(same=40,nop=1),
            row(body=0),
            row(dispatch=0),
            row(caller=0),
            row(unmapped=1),
            row(direct=0)
        ):
            with self.subTest(data=data):
                summary,ready=inspect(data)
                self.assertFalse(ready)
                self.assertIn("ready=0",summary)

    def test_ambiguous_and_bad_original_rejected(self):
        with self.assertRaisesRegex(ValueError,"audit_rows"):
            inspect(row()+"\n"+row())
        with self.assertRaisesRegex(ValueError,"audit_rows"):
            inspect("not a SHA-pinned original")
        with self.assertRaisesRegex(ValueError,"symbol_size"):
            inspect(row().replace("words=41","words=42"))

if __name__=="__main__":
    unittest.main()
