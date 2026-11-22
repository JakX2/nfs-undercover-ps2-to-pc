#!/usr/bin/env python3
"""V333 tests use synthetic public marker lines only."""
from pathlib import Path
import tempfile
import unittest

from analyze_v333_nand_cache_native import DONE,inspect
from diagnose_v299_native_log import WINDOW

class Tests(unittest.TestCase):
    def test_completion_is_distinct_from_guest_entry(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"private.log"
            p.write_text(
                "V289_NAND_ENTRY n=1 phase=0 zero=1 sc=1 guest=1 inst=100\n"
                "V296_SERVICE_ENTRY kind=1 guest=1 direct=1 inst=110\n"
                +DONE+"\n"
                +"what(): SECRET_GUEST_STRING\n",
                encoding="utf-8"
            )
            row=inspect(p,134)
            self.assertIn("rc=134 kind=signal size_band=0 complete=1",row)
            self.assertIn("child=1 early=1 late=0 writer=0 sc_done=1",row)
            self.assertNotIn("SECRET_GUEST_STRING",row)
            self.assertNotIn(str(p),row)

    def test_partial_entry_does_not_imply_completion(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"private.log"
            p.write_text(
                "V289_NAND_ENTRY n=2 phase=0 zero=1 sc=1 guest=1 inst=10\n"
                "V331_NAND_CACHE_SYSCALL verified=1 extra data\n"
                "prefix V331_NAND_CACHE_SYSCALL verified=1\n",
                encoding="utf-8"
            )
            row=inspect(p,124)
            self.assertIn("kind=timeout",row)
            self.assertIn("child=1 early=0 late=0 writer=0 sc_done=0",row)

    def test_late_service_and_writer_not_synthesized(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"private.log"
            p.write_text(
                "V296_SERVICE_ENTRY kind=2 guest=1 direct=0 inst=500\n"
                "V278_FCA4_ENTRY n=1 phase=1 cb=1 nand=1 child=1 sc=3 guest=1 inst=600\n"
                +DONE+"\n"+DONE+"\n",
                encoding="utf-8"
            )
            row=inspect(p,0)
            self.assertIn("kind=zero",row)
            self.assertIn("child=0 early=0 late=1 writer=1 sc_done=2",row)

    def test_incomplete_sample_marks_uncertainty(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"private.log"
            with p.open("wb") as out:
                out.write((DONE+"\n").encode())
                out.seek(WINDOW+512)
                out.write(b"\nunrelated\n")
            row=inspect(p,124)
            self.assertIn("complete=0",row)
            self.assertIn("sc_done=1",row)

    def test_invalid_return_code_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"private.log"
            p.write_text("",encoding="utf-8")
            for rc in (-1,256):
                with self.assertRaises(ValueError):
                    inspect(p,rc)

if __name__=="__main__":
    unittest.main()
