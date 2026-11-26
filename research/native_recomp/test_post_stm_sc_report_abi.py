#!/usr/bin/env python3
import unittest
from prepare_post_stm_sc_report_abi import model
B=0x80001000;T=0x80002000
def ins(op,rs,ra,n):return (op<<26)|(rs<<21)|(ra<<16)|(n&0xffff)
def bl(pc,dst):return 0x48000001|((dst-pc)&0x03fffffc)
def fixture():
    w=[ins(37,1,1,-128),0x7c0802a6,ins(36,0,1,132)]
    w.extend(ins(36,i,1,32+4*(i-3)) for i in range(3,11))
    w.extend((ins(15,0,0,0x100),ins(36,0,1,8),ins(14,0,1,136),ins(36,0,1,12),
              ins(14,0,1,32),ins(36,0,1,16),ins(14,4,1,8)))
    return tuple(w)+(bl(B+4*len(w),T),)
class Abi(unittest.TestCase):
    def test_va_list(self):
        w=fixture()
        self.assertEqual(model(B,w),(len(w),13,8,128,T))
        for i,replacement in ((3,ins(36,4,1,32)),(11,ins(15,0,0,0x200)),(13,ins(14,0,1,140)),
                              (15,ins(14,0,1,36)),(17,ins(14,4,1,12))):
            bad=list(w);bad[i]=replacement
            with self.subTest(i=i),self.assertRaises(ValueError):model(B,tuple(bad))
if __name__=='__main__':unittest.main(verbosity=2)
