#!/usr/bin/env python3
import unittest
from prepare_post_stm_sc_report_formatter import closure
B=0x80001000
class Formatter(unittest.TestCase):
    def test_bounds(self):
        words=(0x2c030000,0x41820008,0x48001001,0x4e800020)
        seen,bounds,back=closure(B,words)
        self.assertEqual((len(seen),len(bounds),back),(4,2,0))
        for bad in ((0x48001000,), (0x60000000,), (0x48000000,)):
            with self.assertRaises(ValueError):closure(B,bad)
if __name__=='__main__':unittest.main(verbosity=2)
