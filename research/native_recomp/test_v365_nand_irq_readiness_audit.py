#!/usr/bin/env python3
"""V365 no proprietary files, original-free IRQ readiness census tests."""
import tempfile
import unittest
from pathlib import Path
from analyze_v365_nand_irq_readiness import inspect
from diagnose_v299_native_log import WINDOW

def check(log:str,rc:int=134)->str:
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/"secret.log"
        path.write_text(log,encoding="utf-8")
        return inspect(path,rc)

class Tests(unittest.TestCase):
    def test_original_vector_ready_after_ee_and_irq_are_both_set(self):
        row=check(
            "PRIVATE_SOURCE_DO_NOT_PUBLISH\n"
            "V365_IRQ_READY n=1 eligible=0 safe=1 installed=1 ready=0\n"
            "V365_IRQ_READY n=2 eligible=1 safe=1 installed=1 ready=1\n"
        )
        self.assertIn("samples=2 eligible_any=1 safe_any=1 installed_any=1 ready_any=1",row)
        self.assertNotIn("PRIVATE_SOURCE_DO_NOT_PUBLISH",row)
        self.assertNotIn("secret.log",row)

    def test_irq_pending_but_ee_masked_is_not_ready(self):
        row=check("V365_IRQ_READY n=1 eligible=0 safe=1 installed=1 ready=0\n")
        self.assertIn("samples=1 eligible_any=0 safe_any=1 installed_any=1 ready_any=0",row)

    def test_non_safe_or_corrupted_vector_does_not_count_ready(self):
        row=check(
            "V365_IRQ_READY n=1 eligible=1 safe=0 installed=1 ready=0\n"
            "V365_IRQ_READY n=2 eligible=1 safe=1 installed=0 ready=0\n"
        )
        self.assertIn("samples=2 eligible_any=1 safe_any=1 installed_any=1 ready_any=0",row)

    def test_fake_ready_marker_is_not_counted(self):
        row=check(
            "prefix V365_IRQ_READY n=1 eligible=1 safe=1 installed=1 ready=1\n"
            "V365_IRQ_READY n=0 eligible=1 safe=1 installed=1 ready=1\n"
            "V365_IRQ_READY n=1 eligible=0 safe=0 installed=0 ready=1\n"
        )
        self.assertIn("samples=0",row)

    def test_gaps_do_not_invent_complete_window(self):
        row=check(
            "V365_IRQ_READY n=1 eligible=1 safe=1 installed=1 ready=1\n"
            "V365_IRQ_READY n=3 eligible=0 safe=1 installed=1 ready=0\n"
        )
        self.assertIn("samples=1 eligible_any=1 safe_any=1 installed_any=1 ready_any=1",row)

    def test_truncated_log_does_not_claim_coverage(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"secret.log"
            with path.open("wb") as f:
                f.write(b"V365_IRQ_READY n=1 eligible=1 safe=1 installed=1 ready=1\n")
                f.seek(WINDOW+400)
                f.write(b"\nend\n")
            row=inspect(path,124)
            self.assertIn("sample_complete=0 samples=1",row)

    def test_unacceptable_exit_code(self):
        for rc in (-1,256):
            with self.assertRaises(ValueError):
                check("",rc)

if __name__=="__main__":
    unittest.main()
