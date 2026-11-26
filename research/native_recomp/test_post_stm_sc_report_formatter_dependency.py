#!/usr/bin/env python3
import unittest
from prepare_post_stm_sc_report_formatter_dependency import census
B=0x80001000
class Census(unittest.TestCase):
    def test_leaf(self):
        ws=(0x88630000,0x2c030000,0x41820008,0x38600001,0x4e800020)
        n,ret,other,back,calls,mem,ops=census(B,ws)
        self.assertEqual((n,ret,other,back,calls),(5,1,0,0,()))
        self.assertEqual(mem,{'load_argument':1})
        self.assertEqual(ops,{'load_1':1,'cmp_imm':1,'bc_cr':1,'add_imm':1,'return':1})
        with self.assertRaises(ValueError):census(B,(0x60000000,))
if __name__=='__main__':unittest.main(verbosity=2)
