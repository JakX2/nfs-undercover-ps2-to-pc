#!/usr/bin/env python3
"""V307 synthetic-only native abort provenance and privacy tests."""
from pathlib import Path
import tempfile
import unittest

from analyze_v307_helper_abort import inspect

SOURCE='static void check(bool ok, const char* msg); check(false,"Public helper assertion");'
BASE=(
    "V250_CB_BEGIN candidate=1 reply=1 captured=1\n"
    "V289_NAND_ENTRY n=1 phase=0 zero=1 sc=1 guest=1 inst=100\n"
    "V296_SERVICE_ENTRY kind=1 guest=1 direct=1 inst=121\n"
)

class Tests(unittest.TestCase):
    def test_known_public_assertion(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"private.log"
            p.write_text(BASE+
                "terminate called after throwing an instance of 'std::runtime_error'\n"
                "what(): Public helper assertion\n")
            row,claim=inspect(p,SOURCE,134)
            self.assertIn("rc=134 kind=signal size_band=0",row)
            self.assertIn("callback=1 child=1 early=1",row)
            self.assertIn("public_id=0001 known=1 exception=runtime",row)
            self.assertIn("label=Public helper assertion",claim)

    def test_unknown_private_text_not_leaked(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"private.log"
            p.write_text(BASE+"what(): SECRET_PRIVATE_STUFF\n")
            row,claim=inspect(p,SOURCE,124)
            self.assertIn("kind=timeout",row)
            self.assertIn("public_id=0000 known=0",row)
            self.assertIn("label=other",claim)
            self.assertNotIn("SECRET_PRIVATE_STUFF",row+claim)
            self.assertNotIn(str(p),row+claim)

    def test_invalid_inputs_fail_closed(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"private.log"
            p.write_text(BASE)
            with self.assertRaises(ValueError):
                inspect(p,SOURCE,-1)
            with self.assertRaises(ValueError):
                inspect(p,"",134)

if __name__=="__main__":
    unittest.main()
