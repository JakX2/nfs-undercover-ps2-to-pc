#!/usr/bin/env python3
"""V370 original-free Hollywood W1C log classification tests."""
import tempfile
import unittest
from pathlib import Path
from analyze_v370_nand_ipc_flag import inspect
from diagnose_v299_native_log import WINDOW

def run(value:str,rc:int=134)->str:
    with tempfile.TemporaryDirectory() as d:
        path=Path(d)/"secret.log"
        path.write_text(value,encoding="utf-8")
        return inspect(path,rc)

class Tests(unittest.TestCase):
    def test_actual_guest_w1c_clears_latch_without_publishing_reply(self):
        line=(
            "PRIVATE_GUEST_DATA\n"
            "V370_NAND_FLAG_W1C n=1 accepted=1 before=1 write_ipc=1 "
            "remaining=0 irq=0 queued=1\n"
        )
        result=run(line)
        self.assertIn("writes=1 accepted=1 ipc_write=1 cleared=1 queued_any=1 irq_any=0",result)
        self.assertNotIn("PRIVATE_GUEST_DATA",result)
        self.assertNotIn("secret.log",result)

    def test_non_ipc_w1c_is_not_counted_as_ipc_ack(self):
        result=run("V370_NAND_FLAG_W1C n=1 accepted=1 before=1 write_ipc=0 remaining=1 irq=1 queued=1\n")
        self.assertIn("writes=1 accepted=1 ipc_write=0 cleared=0 queued_any=1 irq_any=1",result)

    def test_no_writer_is_not_a_completion_claim(self):
        self.assertIn("writes=0 accepted=0 ipc_write=0 cleared=0",run("unrelated\n",0))

    def test_invalid_or_prefixed_marker_does_not_count(self):
        result=run(
            "prefix V370_NAND_FLAG_W1C n=1 accepted=1 before=1 write_ipc=1 remaining=0 irq=0 queued=1\n"
            "V370_NAND_FLAG_W1C n=0 accepted=1 before=1 write_ipc=1 remaining=0 irq=0 queued=1\n"
            "V370_NAND_FLAG_W1C n=1 accepted=1 before=1 write_ipc=1 remaining=2 irq=0 queued=1\n"
        )
        self.assertIn("writes=0",result)

    def test_impossible_latch_state_breaks_contiguous_prefix(self):
        result=run("V370_NAND_FLAG_W1C n=1 accepted=1 before=1 write_ipc=1 remaining=1 irq=1 queued=1\n")
        self.assertIn("writes=0",result)

    def test_missing_sequence_is_not_joined_across_gap(self):
        result=run(
            "V370_NAND_FLAG_W1C n=1 accepted=1 before=1 write_ipc=1 remaining=0 irq=0 queued=1\n"
            "V370_NAND_FLAG_W1C n=3 accepted=1 before=1 write_ipc=1 remaining=0 irq=0 queued=1\n"
        )
        self.assertIn("writes=1 accepted=1",result)

    def test_truncated_private_log_is_flagged(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"secret.log"
            with p.open("wb") as stream:
                stream.write(
                    b"V370_NAND_FLAG_W1C n=1 accepted=1 before=1 write_ipc=1 remaining=0 irq=0 queued=1\n"
                )
                stream.seek(WINDOW+300)
                stream.write(b"\nend\n")
            result=inspect(p,124)
            self.assertIn("sample_complete=0 writes=1",result)

    def test_invalid_exit_code_rejected(self):
        for rc in (-1,256):
            with self.assertRaises(ValueError):
                run("",rc)

if __name__=="__main__":
    unittest.main()
