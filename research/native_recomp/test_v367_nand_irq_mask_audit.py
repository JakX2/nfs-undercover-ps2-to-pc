#!/usr/bin/env python3
"""V367 original-free bounded native mask route evidence."""
import tempfile
import unittest
from pathlib import Path
from analyze_v367_nand_irq_mask import inspect
from diagnose_v299_native_log import WINDOW

def run(text:str,rc:int=134)->str:
    with tempfile.TemporaryDirectory() as d:
        p=Path(d)/"private.log"
        p.write_text(text,encoding="utf-8")
        return inspect(p,rc)

class Tests(unittest.TestCase):
    def test_real_pi_and_hollywood_writes_classified_without_raw_values(self):
        row=run(
            "PRIVATE_GUEST_OPCODE\n"
            "V367_NAND_IRQ_MASK n=1 kind=2 accepted=1 irq=1\n"
            "V367_NAND_IRQ_MASK n=2 kind=1 accepted=1 irq=0\n"
        )
        self.assertIn("writes=2 pi=1 ppc=1 accepted=2 irq_any=1",row)
        self.assertNotIn("PRIVATE_GUEST_OPCODE",row)
        self.assertNotIn("private.log",row)

    def test_no_writer_marker_is_not_success(self):
        self.assertIn("writes=0 pi=0 ppc=0 accepted=0 irq_any=0",run("none\n"))

    def test_bad_markers_do_not_invent_real_writes(self):
        row=run(
            "prefix V367_NAND_IRQ_MASK n=1 kind=2 accepted=1 irq=1\n"
            "V367_NAND_IRQ_MASK n=0 kind=2 accepted=1 irq=1\n"
            "V367_NAND_IRQ_MASK n=1 kind=3 accepted=1 irq=1\n"
            "V367_NAND_IRQ_MASK n=1 kind=1 accepted=2 irq=1\n"
        )
        self.assertIn("writes=0",row)

    def test_rejected_hardware_write_is_not_counted_as_accepted(self):
        row=run("V367_NAND_IRQ_MASK n=1 kind=1 accepted=0 irq=0\n")
        self.assertIn("writes=1 pi=1 ppc=0 accepted=0",row)

    def test_duplicate_or_skipped_sequence_does_not_extend_prefix(self):
        row=run(
            "V367_NAND_IRQ_MASK n=1 kind=2 accepted=1 irq=1\n"
            "V367_NAND_IRQ_MASK n=3 kind=2 accepted=1 irq=1\n"
        )
        self.assertIn("writes=1 pi=0 ppc=1 accepted=1",row)

    def test_partial_sample_is_explicitly_limited(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"private.log"
            with p.open("wb") as f:
                f.write(b"V367_NAND_IRQ_MASK n=1 kind=1 accepted=1 irq=0\n")
                f.seek(WINDOW+200)
                f.write(b"\nend\n")
            row=inspect(p,124)
            self.assertIn("sample_complete=0 writes=1",row)

    def test_invalid_exit_code_rejected(self):
        for rc in (-1,256):
            with self.assertRaises(ValueError):
                run("",rc)

if __name__=="__main__":
    unittest.main()
