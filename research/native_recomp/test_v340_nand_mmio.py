#!/usr/bin/env python3
"""V340 classifier uses synthetic fixed-format lines only."""
from pathlib import Path
import tempfile
import unittest
from analyze_v340_nand_mmio import inspect
from diagnose_v299_native_log import WINDOW

class Tests(unittest.TestCase):
    def test_nand_mmio_categories_and_no_raw_leak(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"private.log"
            p.write_text(
                "SENSITIVE_REQUEST_CONTENTS\n"
                "V340_NAND_MMIO n=1 kind=3 ack=1 submit=1 send=1 readable=1\n"
                "V340_NAND_MMIO n=2 kind=1 ack=1 submit=1 send=1 readable=1\n"
                "V340_NAND_MMIO n=3 kind=2 ack=1 submit=1 send=1 readable=1\n"
                "V340_NAND_MMIO n=4 kind=4 ack=1 submit=1 send=1 readable=1\n"
                "V340_NAND_MMIO n=5 kind=0 ack=0 submit=0 send=0 readable=0\n",
                encoding="utf-8")
            row=inspect(p,134)
            self.assertIn("kind=signal size_band=0 sample_complete=1 observed=5",row)
            self.assertIn("other=1 msg=1 ctrl=1 mask=1 flag=1",row)
            self.assertIn("old_ack=1 old_submit=1 old_send=1 readable=4",row)
            self.assertNotIn("SENSITIVE_REQUEST_CONTENTS",row)
            self.assertNotIn(str(p),row)
    def test_corrupt_or_prefixed_marker_is_not_counted(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"private.log"
            p.write_text(
                "prefix V340_NAND_MMIO n=1 kind=1 ack=1 submit=1 send=1 readable=1\n"
                "V340_NAND_MMIO n=0 kind=1 ack=1 submit=1 send=1 readable=1\n"
                "V340_NAND_MMIO n=17 kind=1 ack=1 submit=1 send=1 readable=1\n"
                "V340_NAND_MMIO n=1 kind=99 ack=1 submit=1 send=1 readable=1\n"
                "V340_NAND_MMIO n=1 kind=1 ack=2 submit=1 send=1 readable=1\n",
                encoding="utf-8")
            row=inspect(p,124)
            self.assertIn("observed=0 other=0 msg=0 ctrl=0 mask=0 flag=0",row)
    def test_partial_sample_not_negative_proof(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"private.log"
            with p.open("wb") as out:
                out.write(b"V340_NAND_MMIO n=1 kind=1 ack=1 submit=1 send=0 readable=1\n")
                out.seek(WINDOW+450)
                out.write(b"\nunrelated\n")
            row=inspect(p,124)
            self.assertIn("sample_complete=0 observed=1",row)
    def test_invalid_return_code_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"private.log"
            p.write_text("",encoding="utf-8")
            for rc in (-1,256):
                with self.assertRaises(ValueError):
                    inspect(p,rc)

if __name__=="__main__":
    unittest.main()
