#!/usr/bin/env python3
import unittest
from prepare_post_stm_sc_report_helper_prefix import prefix
B=0x80001000;T=0x80002000
def ins(op,rs,ra,n):return (op<<26)|(rs<<21)|(ra<<16)|(n&0xffff)
def bl(pc,dst):return 0x48000001|((dst-pc)&0x03fffffc)
def mr(ra,rs):return (31<<26)|(rs<<21)|(ra<<16)|(rs<<11)|(444<<1)
class Prefix(unittest.TestCase):
    def test_prefix(self):
        ws=(ins(37,1,1,-32),0x7c0802a6,ins(36,0,1,36),ins(36,31,1,28),mr(31,3),
            bl(B+20,T),ins(32,31,1,28),ins(32,0,1,36),0x7c0803a6,ins(14,1,1,32),0x4e800020)
        self.assertEqual(prefix(B,ws),(6,32,3,0,{-4:31},T))
        for i,replacement in ((0,ins(37,1,1,-4)),(2,ins(36,0,1,24)),(3,ins(36,30,1,28)),
                              (4,ins(32,31,13,0))):
            bad=list(ws);bad[i]=replacement
            with self.subTest(i=i),self.assertRaises(ValueError):prefix(B,tuple(bad))
if __name__=='__main__':unittest.main(verbosity=2)
