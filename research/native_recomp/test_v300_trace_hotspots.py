#!/usr/bin/env python3
"""V300 original-free sanitized trace marker and PC histogram tests."""
from pathlib import Path
import tempfile
import unittest

from analyze_v300_trace_hotspots import analyze
from diagnose_v299_native_log import WINDOW, PRIOR_LIMIT

PUBLIC='''std::cout<<"V178_IPC_DEP phase=";
std::cout<<"V289_NAND_ENTRY n=";
std::cout<<"V296_SERVICE_ENTRY kind=";'''

class Tests(unittest.TestCase):
    def test_public_marker_and_pc_count(self):
        log=(
            "V178_IPC_DEP phase=1 pc=8051d20c lr=8052fab4\n"
            "V178_IPC_DEP phase=1 pc=8051d20c lr=8052fab4\n"
            "V289_NAND_ENTRY n=1 phase=0 zero=1 sc=1 guest=1 inst=100\n"
            "GAME_PRIVATE unknown data pc=8051d20c\n"
        )
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"private.log"
            path.write_text(log,encoding="utf-8")
            rows=analyze(path,PUBLIC)
            self.assertIn("matched=3 unmatched=1 distinct=2 distinct_pc=1",rows[0])
            self.assertIn("name=V178_IPC_DEP hits=2",rows[1])
            self.assertIn("pc=8051d20c hits=2",rows[-1])
            self.assertNotIn("GAME_PRIVATE","\n".join(rows))

    def test_untrusted_marker_not_in_public_catalog(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"private.log"
            path.write_text("V911_SECRET_PAYLOAD pc=8052fa60\n",encoding="utf-8")
            row=analyze(path,PUBLIC)[0]
            self.assertIn("matched=0 unmatched=1 distinct=0",row)

    def test_large_log_edge_bounded(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"private.log"
            with path.open("wb") as stream:
                stream.write(b"V178_IPC_DEP phase=1 pc=8051d20c\n")
                stream.seek(PRIOR_LIMIT+WINDOW)
                stream.write(b"\nV296_SERVICE_ENTRY kind=1 guest=1 direct=1 inst=90\n")
            output=analyze(path,PUBLIC)
            self.assertIn("size_band=2",output[0])
            self.assertIn("matched=2",output[0])
            self.assertLess(sum(map(len,output)),4096)

    def test_invalid_harness_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"private.log"
            path.write_text("something else")
            with self.assertRaises(ValueError):
                analyze(path,"")
            with self.assertRaises(ValueError):
                analyze(path,"x"*24_000_001)

if __name__=="__main__":
    unittest.main()
