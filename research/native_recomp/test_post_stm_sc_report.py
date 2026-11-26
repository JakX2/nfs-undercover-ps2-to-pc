#!/usr/bin/env python3
import unittest
from prepare_post_stm_sc_report import report_prefix
B=0x80001000;T=0x80002000
def ins(op,rs,ra,n):return (op<<26)|(rs<<21)|(ra<<16)|(n&0xffff)
def bl(pc,dst):return 0x48000001|((dst-pc)&0x03fffffc)
class Report(unittest.TestCase):
    def test_cr6_clear(self):
        # Independent synthetic frame and CR6-only branch over FP spill.
        words=(ins(37,1,1,-64),0x40860008,ins(54,1,1,16),ins(36,3,1,24),bl(B+16,T))
        # bne CR1 (CR bit 6 clear) skips the FP spill.
        self.assertEqual(report_prefix(B,words),(5,4,2,0,64,T))
        for bad in ((words[0],words[1]^(1<<16),*words[2:]),
                    (words[0],words[1],words[2],ins(36,3,1,0),words[4]),
                    (ins(37,1,1,-4),*words[1:])):
            with self.assertRaises(ValueError):report_prefix(B,bad)
if __name__=='__main__':unittest.main(verbosity=2)
