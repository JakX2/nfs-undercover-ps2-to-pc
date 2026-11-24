#!/usr/bin/env python3
import unittest
from apply_stm_native_open_v632 import OLD,NEW,rewrite
class ScopedNativeOpen(unittest.TestCase):
    def test_rewrite(self):
        original="before\n"+OLD+"\nafter\n"
        self.assertEqual(rewrite(original),"before\n"+NEW+"\nafter\n")
        self.assertEqual(rewrite(rewrite(original)),rewrite(original))
        self.assertIn("0x80519944u",NEW)
    def test_refuse(self):
        for source in ("",OLD+"\n"+OLD,NEW+"\n"+OLD):
            with self.assertRaises(ValueError):rewrite(source)
if __name__=="__main__":unittest.main()
