#!/usr/bin/env python3
"""Synthetic no-owner regression for bounded PPC startup tail metadata."""
import contextlib
import io
import struct
import unittest
from unittest.mock import patch
from probe_startup_tail_v90 import tail,MAX_TAIL
class TailTests(unittest.TestCase):
    def test_metadata(self):
        pc=0x80010000
        call=0x48000001|0x20
        code=struct.pack(">III",call,0x60000000,0x4e800020)
        with patch("probe_startup_tail_v90.get_text",return_value=code),contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(tail(b"",{pc:12},pc,pc),[(pc,pc+32)])
        self.assertIn("V90_CALL",out.getvalue())
        self.assertIn("V90_RETURN",out.getvalue())
        self.assertNotIn("48000021",out.getvalue())
    def test_reject_bad_span(self):
        with self.assertRaises(ValueError):
            tail(b"",{0x8000:MAX_TAIL+4},0x8000,0x8000)
        with self.assertRaises(ValueError):
            tail(b"",{0x8000:4},0x8000,0x8004)
if __name__=="__main__":
    unittest.main()
