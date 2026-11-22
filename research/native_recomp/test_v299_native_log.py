#!/usr/bin/env python3
"""V299 original-free bounded native log edge-sampling tests."""
import tempfile
from pathlib import Path
import unittest

from diagnose_v299_native_log import (
    WINDOW, PRIOR_LIMIT, category, diagnose, read_edges, size_band
)

CALLBACK = b"V250_CB_BEGIN candidate=1 reply=1 captured=1\n"
CHILD = b"V289_NAND_ENTRY n=1 phase=0 zero=1 sc=1 guest=1 inst=77\n"
SERVICE = b"V296_SERVICE_ENTRY kind=1 guest=1 direct=1 inst=98\n"

class Tests(unittest.TestCase):
    def test_exit_and_band_categories(self):
        self.assertEqual([category(i) for i in (0, 1, 124, 126, 134)],
                         ["zero", "nonzero", "timeout", "launch", "signal"])
        self.assertEqual([size_band(i) for i in
                          (0, 1_000_001, PRIOR_LIMIT+1, 64_000_001)],
                         [0, 1, 2, 3])
        with self.assertRaises(ValueError):
            category(-11)
        with self.assertRaises(ValueError):
            size_band(-1)

    def test_small_log_and_no_untrusted_output(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)/"private.log"
            path.write_bytes(CALLBACK + CHILD + SERVICE + b"untrusted address 0xdeadbeef\n")
            result = diagnose(path, 134)
            self.assertIn("kind=signal size_band=0 over_limit=0", result)
            self.assertIn("callback=1 child=1 early=1 late=0", result)
            self.assertNotIn("deadbeef", result)
            self.assertNotIn(str(path), result)

    def test_oversized_sparse_log_only_samples_edges(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)/"huge.log"
            with path.open("wb") as stream:
                stream.write(CALLBACK)
                stream.seek(PRIOR_LIMIT + WINDOW)
                stream.write(b"\n"+SERVICE)
            report = diagnose(path, 124)
            self.assertIn("kind=timeout size_band=2 over_limit=1", report)
            self.assertIn("callback=1 child=0 early=1", report)
            size, lines = read_edges(path)
            self.assertGreater(size, PRIOR_LIMIT)
            self.assertLess(sum(map(len, lines)), 2 * WINDOW)

    def test_partial_sample_records_dropped(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)/"partial.log"
            path.write_bytes(CALLBACK + b"x"*WINDOW + b"garbage\n" + SERVICE)
            report = diagnose(path, 1)
            self.assertIn("kind=nonzero", report)
            self.assertIn("early=1", report)
            self.assertNotIn("garbage", report)

if __name__ == "__main__":
    unittest.main()
