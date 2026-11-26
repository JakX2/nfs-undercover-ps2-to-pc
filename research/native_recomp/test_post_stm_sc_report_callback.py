#!/usr/bin/env python3
import unittest
from prepare_post_stm_sc_report_callback import census
B=0x80001000;T=0x80002000
class Callback(unittest.TestCase):
    def test_bounds(self):
        ws=(0x2c030000,0x41820008,0x48000001|((T-(B+8))&0x03fffffc),0x4e800020)
        n,k,b,terms=census(B,ws)
        self.assertEqual((n,b,terms),(4,0,[('direct',T),('return',0)]))
        with self.assertRaises(ValueError):census(B,(0x48010000,))
if __name__=='__main__':unittest.main(verbosity=2)
