#!/usr/bin/env python3
import unittest
from prepare_post_stm_sc_report_helper import census
B=0x80001000;T=0x80002000
def bl(pc,dst):return 0x48000001|((dst-pc)&0x03fffffc)
class Helper(unittest.TestCase):
    def test_census(self):
        ws=(0x9421ffe0,0x7c0802a6,0x90010024,bl(B+12,T),0x80010024,0x38210020,0x4e800020)
        edges,reach,returns,first,counts,loads,stores,back=census(B,ws)
        self.assertEqual(edges,{B+12:T});self.assertEqual(len(reach),7)
        self.assertEqual(returns,{B+24});self.assertEqual(first,B+12)
        self.assertEqual((counts['direct'],loads,stores,back),(1,1,2,0))
        for bad in (ws[:-1],(*ws[:2],0x44000002,*ws[3:]),(*ws[:3],0x48000020,*ws[4:])):
            with self.assertRaises(ValueError):census(B,bad)
if __name__=='__main__':unittest.main(verbosity=2)
