#!/usr/bin/env python3
import unittest
from prepare_post_stm_sc_report_helper_suffix import model
B=0x80001000;T=0x80002000;U=0x80003000
def bl(pc,dst):return 0x48000001|((dst-pc)&0x03fffffc)
class Suffix(unittest.TestCase):
    def test_return(self):
        words=(0x9421ffe0,bl(B+4,T),0x2c030000,0x41820008,bl(B+16,U),
               0x80010024,0x83e1001c,0x7c0803a6,0x38210020,0x4e800020)
        slots=((4,32),(-4,31))
        self.assertEqual(model(B,words,slots,32),(8,1,2,5,2,1))
        for bad in ((*words[:6],0x83e10018,*words[7:]),(*words[:8],0x3821001c,words[-1])):
            with self.assertRaises(ValueError):model(B,bad,slots,32)
if __name__=='__main__':unittest.main(verbosity=2)
