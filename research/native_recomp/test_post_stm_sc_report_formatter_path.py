#!/usr/bin/env python3
import unittest
from prepare_post_stm_sc_report_formatter_path import first_path,const
B=0x80001000;T=0x80002000;A=0x80003000
def bl(pc,dst):return 0x48000001|((dst-pc)&0x03fffffc)
class Path(unittest.TestCase):
    def test_path(self):
        ws=(0x9421ffe0,0x7c0802a6,0x90010024,0x93e1001c,0x88830000,0x2c040041,0x40820008,bl(B+28,T),0x4e800020)
        path,frame,accesses,saved,dst,*_=first_path(B,ws,{3:const(A)},{},((A,b'A\0'),))
        self.assertEqual((len(path),frame,len(accesses),saved,dst),(8,32,4,1,T))
        for bad in ((0x9421fffc,*ws[1:]),(*ws[:2],0x90010004,*ws[3:]),(*ws[:4],0x88830004,*ws[5:])):
            with self.assertRaises(ValueError):first_path(B,bad,{3:const(A)},{},((A,b'A\0'),))
if __name__=='__main__':unittest.main(verbosity=2)
