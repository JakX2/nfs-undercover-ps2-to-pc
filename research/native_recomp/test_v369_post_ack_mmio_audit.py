#!/usr/bin/env python3
"""V369 original-free post-ACK MMIO category evidence."""
import tempfile
import unittest
from pathlib import Path
from analyze_v369_post_ack_mmio import inspect
from diagnose_v299_native_log import WINDOW

def run(content:str,rc:int=134)->str:
    with tempfile.TemporaryDirectory() as td:
        file=Path(td)/"secret.log"
        file.write_text(content,encoding="utf-8")
        return inspect(file,rc)

class Tests(unittest.TestCase):
    def test_known_post_ack_classes_and_legacy_observer(self):
        line=(
            "PRIVATE_ADDR_AND_OPCODE\n"
            "V369_POST_ACK_MMIO n=1 kind=2 legacy=1 readable=1 irq=1\n"
            "V369_POST_ACK_MMIO n=2 kind=3 legacy=1 readable=1 irq=0\n"
            "V369_POST_ACK_MMIO n=3 kind=4 legacy=1 readable=1 irq=0\n"
        )
        row=run(line)
        self.assertIn("writes=3 kindmask=1c last=4 mask=1 flag=1 ctrl=1 msg=0 other=0",row)
        self.assertIn("legacy_any=1 readable_any=1 irq_any=1",row)
        self.assertNotIn("PRIVATE_ADDR_AND_OPCODE",row)
        self.assertNotIn("secret.log",row)

    def test_unknown_write_is_not_hidden_as_known(self):
        row=run("V369_POST_ACK_MMIO n=1 kind=0 legacy=1 readable=0 irq=1\n")
        self.assertIn("writes=1 kindmask=01 last=0 mask=0 flag=0 ctrl=0 msg=0 other=1",row)

    def test_no_evidence_is_not_counted_as_progress(self):
        self.assertIn("writes=0 kindmask=00 last=0",run("unrelated\n",0))

    def test_invalid_records_do_not_count(self):
        row=run(
            "prefix V369_POST_ACK_MMIO n=1 kind=3 legacy=1 readable=1 irq=1\n"
            "V369_POST_ACK_MMIO n=33 kind=3 legacy=1 readable=1 irq=1\n"
            "V369_POST_ACK_MMIO n=1 kind=6 legacy=1 readable=1 irq=1\n"
            "V369_POST_ACK_MMIO n=1 kind=3 legacy=2 readable=1 irq=1\n"
        )
        self.assertIn("writes=0",row)

    def test_gaps_preserve_only_contiguous_prefix(self):
        row=run(
            "V369_POST_ACK_MMIO n=1 kind=1 legacy=1 readable=1 irq=1\n"
            "V369_POST_ACK_MMIO n=3 kind=2 legacy=1 readable=1 irq=1\n"
        )
        self.assertIn("writes=1 kindmask=02 last=1 mask=1",row)

    def test_truncated_sample_is_explicit(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"secret.log"
            with p.open("wb") as stream:
                stream.write(b"V369_POST_ACK_MMIO n=1 kind=5 legacy=0 readable=1 irq=1\n")
                stream.seek(WINDOW+600)
                stream.write(b"\nend\n")
            row=inspect(p,124)
            self.assertIn("sample_complete=0 writes=1 kindmask=20 last=5",row)

    def test_exit_code_guard(self):
        for rc in (-1,256):
            with self.assertRaises(ValueError):
                run("",rc)

if __name__=="__main__":
    unittest.main()
