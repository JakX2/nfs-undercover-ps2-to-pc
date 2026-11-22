#!/usr/bin/env python3
"""V319 synthetic-only guest-entry, sampling, and privacy regression tests."""
from pathlib import Path
import tempfile
import unittest

from audit_v319_native_entries import WINDOW,inspect

class Tests(unittest.TestCase):
    def test_executed_helper_and_allocator_entry(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"native-private.log"
            p.write_text(
                "V98_DEPENDENCY pc=804f2064 lr=8051d20c\n"
                "V98_DEPENDENCY pc=80519bcc lr=804f2070\n"
                "V98_DEPENDENCY pc=8051ad38 lr=80519bd0\n"
                "what(): PRIVATE_DO_NOT_DISCLOSE\n",
                encoding="utf-8"
            )
            row=inspect(p,134)
            self.assertIn("rc=134 kind=signal size_band=0 complete=1",row)
            self.assertIn("known_markers=3 helper41=1 helper64=1",row)
            self.assertIn("allocator_tail=1",row)
            self.assertIn("ios_request=0",row)
            self.assertNotIn("PRIVATE_DO_NOT_DISCLOSE",row)
            self.assertNotIn(str(p),row)

    def test_unknown_addresses_and_malformed_logs_not_treated_as_proof(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"native-private.log"
            p.write_text(
                "V98_DEPENDENCY pc=deadbeef lr=80519bd0\n"
                "V98_DEPENDENCY pc=80519bcc lr=private\n"
                "V98_DEPENDENCY pc=80519bcc lr=80519bd0 unexpected\n"
            )
            row=inspect(p,124)
            self.assertIn("kind=timeout",row)
            self.assertIn("known_markers=0",row)
            self.assertIn("helper64=0",row)

    def test_large_incomplete_sample_does_not_claim_absence(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"native-private.log"
            with p.open("wb") as output:
                output.write(b"V98_DEPENDENCY pc=80519bcc lr=804f2070\n")
                output.seek(WINDOW+1024)
                output.write(b"\nforeign content\n")
            row=inspect(p,124)
            self.assertIn("complete=0",row)
            self.assertIn("helper64=1",row)

    def test_invalid_exit_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"native-private.log"
            p.write_text("")
            with self.assertRaises(ValueError):
                inspect(p,-1)

if __name__=="__main__":
    unittest.main()
