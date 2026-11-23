#!/usr/bin/env python3
"""Original-free strict private marker scan and redaction checks."""
import re
import tempfile
import unittest
from pathlib import Path
from diagnose_v299_native_log import WINDOW,read_edges
from scan_original_guest_markers import MAX_ORIGINAL_LOG_BYTES,scan_original_guest_markers
E=re.compile(r'^V395_TEST_GUEST ok=([01])$')
T=re.compile(r'^V395_TEST_TRIAL ok=([01])$')
class Tests(unittest.TestCase):
    def test_guest_markers_inside_missing_middle_window_are_kept(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'private-wii.log'
            with p.open("wb") as f:
                f.write(b'PRIVATE_BINARY_OUTPUT\n')
                f.write(b'x'*(WINDOW+100))
                f.write(b'\nV395_TEST_GUEST ok=1\nV395_TEST_TRIAL ok=1\n')
                f.write(b'PRIVATE_TRANSLATED_CODE\n')
                f.write(b'y'*(WINDOW+100))
                f.write(b'\n')
            size,lines,overflow=scan_original_guest_markers(p,(E,T))
            self.assertGreater(size,2*WINDOW)
            self.assertEqual(lines,['V395_TEST_GUEST ok=1','V395_TEST_TRIAL ok=1'])
            self.assertFalse(overflow)
            self.assertNotIn('PRIVATE',str(lines))
            self.assertNotIn('V395_TEST_GUEST ok=1',read_edges(p)[1])
    def test_only_fullmatch_ascii_public_markers_retained(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'private-wii.log'
            p.write_bytes(b'V395_TEST_GUEST ok=1 private\nxV395_TEST_GUEST ok=1\n'
                          b'\xffV395_TEST_TRIAL ok=1\nV395_TEST_GUEST ok=0\nV395_TEST_TRIAL ok=1\n')
            _,lines,overflow=scan_original_guest_markers(p,(E,T))
            self.assertEqual(lines,['V395_TEST_GUEST ok=0','V395_TEST_TRIAL ok=1'])
            self.assertFalse(overflow)
    def test_excess_marker_count_is_not_silently_verified(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'private-wii.log'
            p.write_bytes(b'V395_TEST_GUEST ok=1\n'*17)
            _,lines,overflow=scan_original_guest_markers(p,(E,T))
            self.assertEqual(len(lines),16)
            self.assertTrue(overflow)
    def test_overlarge_private_log_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'private-wii.log'
            with p.open('wb') as f:
                f.seek(MAX_ORIGINAL_LOG_BYTES+1)
                f.write(b'\n')
            size,lines,overflow=scan_original_guest_markers(p,(E,))
            self.assertGreater(size,MAX_ORIGINAL_LOG_BYTES)
            self.assertEqual(lines,[])
            self.assertTrue(overflow)
    def test_invalid_scan_limits_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'private.log'
            p.write_bytes(b'')
            for pats,limit in (((),16),((E,),17),((E,),0)):
                with self.assertRaises(ValueError):
                    scan_original_guest_markers(p,pats,limit)
if __name__=="__main__":unittest.main()
