#!/usr/bin/env python3
"""V359 original-free bounded census tests."""
import tempfile
import unittest
from pathlib import Path
from analyze_v359_post_x1_calls import inspect
from diagnose_v299_native_log import WINDOW

def run(text:str,rc:int=134)->str:
    with tempfile.TemporaryDirectory() as td:
        file=Path(td)/"private.log"
        file.write_text(text,encoding="utf-8")
        return inspect(file,rc)

class Tests(unittest.TestCase):
    def test_ordered_positive_guest_calls(self):
        line=(
            "SECRET_GUEST_STATE\n"
            "V359_X1_CALL n=1 kind=1 pending=1 irq=0 ee=0 replies=0\n"
            "V359_X1_CALL n=2 kind=2 pending=1 irq=0 ee=1 replies=0\n"
            "V359_X1_CALL n=3 kind=4 pending=0 irq=1 ee=1 replies=1\n"
        )
        row=run(line)
        self.assertIn("kind=signal size_band=0 sample_complete=1 calls=3",row)
        self.assertIn("kindmask=016",row)
        self.assertIn("pending_first=1 pending_last=0 irq_any=1 ee_any=1 replies_any=1",row)
        self.assertNotIn("SECRET_GUEST_STATE",row)
        self.assertNotIn("private.log",row)

    def test_no_observations_are_not_claimed_as_success(self):
        row=run("other line\n")
        self.assertIn("calls=0 kindmask=000 pending_first=0 pending_last=0",row)

    def test_invalid_or_prefixed_markers_ignored(self):
        row=run(
            "prefix V359_X1_CALL n=1 kind=1 pending=1 irq=0 ee=0 replies=0\n"
            "V359_X1_CALL n=0 kind=1 pending=1 irq=0 ee=0 replies=0\n"
            "V359_X1_CALL n=1 kind=9 pending=1 irq=0 ee=0 replies=0\n"
            "V359_X1_CALL n=1 kind=1 pending=2 irq=0 ee=0 replies=0\n"
        )
        self.assertIn("calls=0 kindmask=000",row)

    def test_gaps_do_not_invent_a_full_trace(self):
        row=run(
            "V359_X1_CALL n=1 kind=3 pending=1 irq=0 ee=0 replies=0\n"
            "V359_X1_CALL n=3 kind=4 pending=0 irq=1 ee=1 replies=1\n"
        )
        self.assertIn("calls=1 kindmask=008 pending_first=1 pending_last=1",row)

    def test_truncated_sample_is_signaled(self):
        with tempfile.TemporaryDirectory() as td:
            file=Path(td)/"private.log"
            with file.open("wb") as stream:
                stream.write(b"V359_X1_CALL n=1 kind=8 pending=1 irq=0 ee=0 replies=0\n")
                stream.seek(WINDOW+700)
                stream.write(b"\nunrelated\n")
            row=inspect(file,124)
            self.assertIn("sample_complete=0 calls=1 kindmask=100",row)

    def test_exit_code_guard(self):
        for rc in (-1,256):
            with self.subTest(rc=rc):
                with self.assertRaises(ValueError):
                    run("",rc)

if __name__=="__main__":
    unittest.main()
