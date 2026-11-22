#!/usr/bin/env python3
"""V304 original-free restored helper execution classifier tests."""
from pathlib import Path
import tempfile
import unittest

from analyze_v304_helper_exec import inspect

LOG=(
    "V250_CB_BEGIN candidate=1 reply=1 captured=1\n"
    "V289_NAND_ENTRY n=1 phase=0 zero=1 sc=1 guest=1 inst=123\n"
    "V296_SERVICE_ENTRY kind=1 guest=1 direct=1 inst=144\n"
    "V98_DEPENDENCY pc=804f2064 lr=8051d21c\n"
    "V104_FALLTHROUGH pc=804f2064 lr=8051d21c phase=1\n"
)

class Tests(unittest.TestCase):
    def test_timeout_and_hotspot_are_only_diagnostics(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"private.log"
            path.write_text(LOG,encoding="utf-8")
            result=inspect(path,124)
            self.assertIn("kind=timeout size_band=0 over_limit=0",result)
            self.assertIn("callback=1 child=1 early=1 late=0 writer=0",result)
            self.assertIn("old_hotspot=2 completed=0",result)

    def test_later_service_and_writer_markers(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"private.log"
            path.write_text(
                LOG +
                "V296_SERVICE_ENTRY kind=2 guest=1 direct=1 inst=170\n"+
                "V278_FCA4_ENTRY n=1 phase=0 cb=1 nand=1 child=1 sc=2 guest=1 inst=190\n"
            )
            result=inspect(path,134)
            self.assertIn("kind=signal",result)
            self.assertIn("late=1 writer=1",result)
            self.assertIn("completed=0",result)

    def test_bad_exit_refused(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"private.log"
            path.write_text("")
            with self.assertRaises(ValueError):
                inspect(path,-11)

if __name__=="__main__":
    unittest.main()
