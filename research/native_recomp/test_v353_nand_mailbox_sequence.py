#!/usr/bin/env python3
"""V353 synthetic marker tests require no retail executable or assets."""
from pathlib import Path
import tempfile
import unittest

from analyze_v353_nand_mailbox_sequence import inspect
from diagnose_v299_native_log import WINDOW

def test_log(text: str, rc=134) -> str:
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/"private.log"
        p.write_text(text,encoding="utf-8")
        return inspect(p,rc)

class Tests(unittest.TestCase):
    def test_real_message_then_x1_control_queues_native_ios(self):
        row=test_log(
            "SENSITIVE_PACKET_DO_NOT_PRINT\n"
            "V352_NAND_BUS kind=1 mapped=1 accepted=1 queued=0\n"
            "V352_NAND_BUS kind=2 mapped=1 accepted=1 queued=1\n"
        )
        self.assertIn("kind=signal size_band=0 sample_complete=1",row)
        self.assertIn("msg=1 ctrl=1 queued=1 invalid=0 chain=2",row)
        self.assertNotIn("SENSITIVE_PACKET_DO_NOT_PRINT",row)
        self.assertNotIn("private.log",row)

    def test_message_acceptance_without_x1_is_not_full_submission(self):
        row=test_log("V352_NAND_BUS kind=1 mapped=1 accepted=1 queued=0\n")
        self.assertIn("msg=1 ctrl=0 queued=0 invalid=0 chain=1",row)

    def test_control_before_message_is_not_ordered_x1(self):
        row=test_log(
            "V352_NAND_BUS kind=2 mapped=1 accepted=1 queued=1\n"
            "V352_NAND_BUS kind=1 mapped=1 accepted=1 queued=1\n"
        )
        self.assertIn("msg=1 ctrl=1 queued=1 invalid=0 chain=1",row)

    def test_invalid_original_pointer_is_not_success(self):
        row=test_log("V352_NAND_BUS kind=1 mapped=0 accepted=0 queued=0\n")
        self.assertIn("msg=0 ctrl=0 queued=0 invalid=1 chain=0",row)

    def test_bus_rejection_is_reported_not_accepted(self):
        row=test_log("V352_NAND_BUS kind=2 mapped=1 accepted=0 queued=0\n")
        self.assertIn("msg=0 ctrl=0 queued=0 invalid=1 chain=0",row)

    def test_malformed_markers_and_impossible_shapes_do_not_count(self):
        row=test_log(
            "V352_NAND_BUS kind=2 mapped=0 accepted=1 queued=1\n"
            "V352_NAND_BUS kind=1 mapped=0 accepted=1 queued=0\n"
            "V352_NAND_BUS kind=1 mapped=1 accepted=2 queued=0\n"
            "prefix V352_NAND_BUS kind=1 mapped=1 accepted=1 queued=0\n"
        )
        self.assertIn("msg=0 ctrl=0 queued=0 invalid=0 chain=0",row)

    def test_incomplete_log_is_not_a_negative_claim(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"private.log"
            with p.open("wb") as f:
                f.write(b"V352_NAND_BUS kind=1 mapped=1 accepted=1 queued=0\n")
                f.seek(WINDOW+500)
                f.write(b"\nnot_a_marker\n")
            row=inspect(p,124)
            self.assertIn("sample_complete=0 msg=1 ctrl=0 queued=0",row)

    def test_unacceptable_rc_rejected(self):
        for rc in (-1,256):
            with self.subTest(rc=rc):
                with self.assertRaises(ValueError):
                    test_log("",rc)

if __name__=="__main__":
    unittest.main()
