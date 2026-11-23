#!/usr/bin/env python3
"""V361 bounded original-free native IOS event classification tests."""
import tempfile
import unittest
from pathlib import Path
from analyze_v361_nand_ios_yield import inspect
from diagnose_v299_native_log import WINDOW

def analyze(log:str,rc:int=134)->str:
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/"private.log"
        path.write_text(log,encoding="utf-8")
        return inspect(path,rc)

class Tests(unittest.TestCase):
    def test_real_ack_is_reported_only_from_native_pump_marker(self):
        row=analyze(
            "SENSITIVE_GUEST_PACKET\n"
            "V361_NAND_IOS_YIELD n=1 mapped=1 pump=1 pending=0 irq=1 eligible=0 replies=1\n"
        )
        self.assertIn("kind=signal size_band=0 sample_complete=1 steps=1",row)
        self.assertIn("first_pump=1 last_pump=1 pending_first=0 pending_last=0",row)
        self.assertIn("irq_any=1 eligible_any=0 replies_any=1",row)
        self.assertNotIn("SENSITIVE_GUEST_PACKET",row)
        self.assertNotIn("private.log",row)

    def test_no_service_is_not_a_claimed_ack(self):
        self.assertIn("steps=0 first_pump=0 last_pump=0",analyze("other\n"))

    def test_multiple_real_transitions_are_bounded(self):
        row=analyze(
            "V361_NAND_IOS_YIELD n=1 mapped=1 pump=1 pending=0 irq=1 eligible=0 replies=1\n"
            "V361_NAND_IOS_YIELD n=2 mapped=1 pump=3 pending=1 irq=1 eligible=1 replies=1\n"
        )
        self.assertIn("steps=2 first_pump=1 last_pump=3",row)
        self.assertIn("irq_any=1 eligible_any=1 replies_any=1",row)

    def test_missing_or_impossible_marker_is_rejected(self):
        row=analyze(
            "prefix V361_NAND_IOS_YIELD n=1 mapped=1 pump=1 pending=0 irq=1 eligible=0 replies=1\n"
            "V361_NAND_IOS_YIELD n=1 mapped=0 pump=1 pending=0 irq=1 eligible=0 replies=1\n"
        )
        self.assertIn("steps=0",row)
        row=analyze("V361_NAND_IOS_YIELD n=1 mapped=1 pump=1 pending=0 irq=0 eligible=1 replies=1\n")
        self.assertIn("steps=0",row)

    def test_gaps_not_reordered(self):
        row=analyze(
            "V361_NAND_IOS_YIELD n=1 mapped=1 pump=1 pending=0 irq=1 eligible=0 replies=1\n"
            "V361_NAND_IOS_YIELD n=3 mapped=1 pump=1 pending=0 irq=1 eligible=1 replies=1\n"
        )
        self.assertIn("steps=1 first_pump=1 last_pump=1",row)

    def test_truncation_signal(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"private.log"
            with p.open("wb") as f:
                f.write(b"V361_NAND_IOS_YIELD n=1 mapped=1 pump=1 pending=0 irq=1 eligible=0 replies=1\n")
                f.seek(WINDOW+500)
                f.write(b"\nfinal\n")
            row=inspect(p,124)
            self.assertIn("sample_complete=0 steps=1",row)

    def test_exit_code_is_not_silently_forged(self):
        for rc in (-1,256):
            with self.assertRaises(ValueError):
                analyze("",rc)

if __name__=="__main__":
    unittest.main()
