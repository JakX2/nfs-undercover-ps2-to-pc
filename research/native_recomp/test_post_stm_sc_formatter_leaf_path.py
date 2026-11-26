#!/usr/bin/env python3
import unittest
from prepare_post_stm_sc_formatter_leaf_path import run,cfg,const
B=0x80001000;A=0x80003000
class Leaf(unittest.TestCase):
    def test_conditional_return(self):
        # cmpwi r4,0; beqlr; lbzu r5,1(r3); cmpwi r5,0; beqlr;
        # addi r3,r3,1; b back to load; blr
        ws=(0x2c040000,0x4d820020,0x8ca30001,0x2c050000,0x4d820020,
            0x38630001,0x4bfffff0,0x4e800020)
        # use a simpler bounded byte search to exercise actual conditional
        # return fallthrough without depending on an unreachable final blr.
        ws=(0x2c040000,0x4d820020,0x88630000,0x2c030041,0x4d820020,0x38600000,0x4e800020)
        gp=[('reg',i) for i in range(32)];gp[3]=const(A);gp[4]=const(0)
        self.assertEqual(len(run(B,ws,gp,((A,b'A'),),{})[0]),2)
        gp[4]=const(1)
        result=run(B,ws,gp,((A,b'A'),),{})
        self.assertEqual((len(result[0]),len(result[1]),result[2]),(5,1,const(65)))
        self.assertEqual(len(cfg(B,ws)[0]),7)
        with self.assertRaises(ValueError):run(B,ws,gp,(),{})
        with self.assertRaises(ValueError):cfg(B,(0x4bfffffc,))
if __name__=='__main__':unittest.main(verbosity=2)
