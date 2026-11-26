#!/usr/bin/env python3
import unittest
from prepare_post_stm_sc_report_dependency import census
B=0x80001000
class Census(unittest.TestCase):
    def test_leaf(self):
        words=(0x80630000,0x2c030000,0x41820008,0x38600001,0x4e800020)
        e,r,ret,c,l,s,b,f=census(B,words)
        self.assertEqual((len(r),len(ret),c['load'],c['branch'],l['argument'],sum(s.values()),b,f),(5,1,1,1,1,0,0,B+8))
        for bad in (words[:-1],(0x44000002,*words[1:]),(*words[:2],0x41820040,*words[3:])):
            with self.assertRaises(ValueError):census(B,bad)
if __name__=='__main__':unittest.main(verbosity=2)
