#!/usr/bin/env python3
"""V321 synthetic one-shot function-entry mask tests."""
from pathlib import Path
import tempfile
import unittest

from derive_v321_guest_entry_probe import TARGETS
from analyze_v321_native_entry_comparison import compare,summarize,WINDOW

class Tests(unittest.TestCase):
    def test_baseline_vs_recovered_descendant_positive_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            base,rest=Path(td)/"baseline-private",Path(td)/"restored-private"
            base.write_text(
                f"V321_GUEST_ENTRY pc={TARGETS[0]:08x}\n"
                "PRIVATE_CPP_SHOULD_NOT_LEAK\n"
            )
            rest.write_text(
                f"V321_GUEST_ENTRY pc={TARGETS[0]:08x}\n"
                f"V321_GUEST_ENTRY pc={TARGETS[1]:08x}\n"
                f"V321_GUEST_ENTRY pc={TARGETS[1]:08x}\n"
            )
            row=compare(base,rest)
            self.assertIn("targets=8 base_mask=01 restored_mask=03",row)
            self.assertIn("added_mask=02 lost_mask=00",row)
            self.assertIn("base_complete=1 restored_complete=1",row)
            self.assertNotIn("PRIVATE_CPP_SHOULD_NOT_LEAK",row)
            self.assertNotIn(str(base),row)

    def test_unknown_malformed_markers_are_ignored(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"log"
            path.write_text(
                "V321_GUEST_ENTRY pc=deadbeef\n"
                "V321_GUEST_ENTRY pc=80519bcc lr=8051d20c\n"
                "V321_GUEST_ENTRY pc=notanaddress\n"
                "V321_GUEST_ENTRY pc=80519bcc\n"
            )
            mask,complete=summarize(path)
            self.assertEqual(mask,2)
            self.assertEqual(complete,1)

    def test_large_log_is_incomplete_even_with_positive_edge(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"private-log"
            with path.open("wb") as f:
                f.write(f"V321_GUEST_ENTRY pc={TARGETS[0]:08x}\n".encode())
                f.seek(WINDOW+2048)
                f.write(b"end\n")
            mask,complete=summarize(path)
            self.assertEqual(mask,1)
            self.assertEqual(complete,0)

if __name__=="__main__":
    unittest.main()
