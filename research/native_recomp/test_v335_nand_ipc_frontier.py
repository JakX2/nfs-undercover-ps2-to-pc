#!/usr/bin/env python3
"""V335 original-free tests use synthetic public marker lines only."""
from pathlib import Path
import tempfile
import unittest

from analyze_v335_nand_ipc_frontier import DONE, TARGETS, inspect
from diagnose_v299_native_log import WINDOW

def marker(pc, lr):
    return f"V98_DEPENDENCY pc={pc:08x} lr={lr:08x}\n"

class Tests(unittest.TestCase):
    def test_exact_ordered_original_ipc_frontier(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "guest.log"
            path.write_text(
                "what(): PRIVATE_TEXT_MUST_NOT_LEAK\n" + DONE + "\n" +
                "".join(marker(pc, lr) for pc, lr in TARGETS),
                encoding="utf-8",
            )
            row = inspect(path, 134)
            self.assertIn("rc=134 kind=signal size_band=0 sample_complete=1", row)
            self.assertIn("sc_done=1 irq=1 queue=1 send=1 ctrl=1 chain=4", row)
            self.assertNotIn("PRIVATE_TEXT_MUST_NOT_LEAK", row)
            self.assertNotIn(str(path), row)

    def test_observed_calls_before_cache_completion_not_a_chain(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "guest.log"
            path.write_text(
                marker(*TARGETS[0]) + DONE + "\n" +
                marker(*TARGETS[1]) + marker(*TARGETS[2]),
                encoding="utf-8",
            )
            row = inspect(path, 124)
            self.assertIn("kind=timeout", row)
            self.assertIn("sc_done=1 irq=1 queue=1 send=1 ctrl=0 chain=0", row)

    def test_partial_order_and_duplicate_markers(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "guest.log"
            path.write_text(
                DONE + "\n" + DONE + "\n" +
                marker(*TARGETS[0]) + marker(*TARGETS[0]) +
                marker(*TARGETS[2]) + marker(*TARGETS[1]),
                encoding="utf-8",
            )
            row = inspect(path, 0)
            self.assertIn("kind=zero", row)
            self.assertIn("sc_done=2 irq=1 queue=1 send=1 ctrl=0 chain=2", row)

    def test_malformed_or_different_callsite_not_a_positive(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "guest.log"
            path.write_text(
                DONE + " EXTRA\n" + "prefix " + DONE + "\n" +
                marker(TARGETS[0][0], 0x80519644) +
                marker(TARGETS[1][0], 0x805196D8) +
                "V98_DEPENDENCY pc=805265ac lr=80519640 suffix\n",
                encoding="utf-8",
            )
            row = inspect(path, 134)
            self.assertIn("sc_done=0 irq=0 queue=0 send=0 ctrl=0 chain=0", row)

    def test_incomplete_bounded_sample_not_negative_proof(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "guest.log"
            with path.open("wb") as out:
                out.write((DONE + "\n" + marker(*TARGETS[0])).encode())
                out.seek(WINDOW + 300)
                out.write(b"\nunrelated\n")
            row = inspect(path, 124)
            self.assertIn("sample_complete=0", row)
            self.assertIn("sc_done=1 irq=1 queue=0 send=0 ctrl=0 chain=1", row)

    def test_invalid_return_code_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "guest.log"
            path.write_text("", encoding="utf-8")
            for invalid in (-1, 256):
                with self.assertRaises(ValueError):
                    inspect(path, invalid)

if __name__ == "__main__":
    unittest.main()
