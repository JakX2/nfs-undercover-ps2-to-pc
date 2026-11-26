#!/usr/bin/env python3
import unittest
from prepare_post_stm_sc_report_dependency_abi import arguments,classify
class Abi(unittest.TestCase):
    def test_args(self):
        r=[('reg',i) for i in range(32)];r[4]=('stack',-120)
        h=[('reg',i) for i in range(32)];h[3]=('reg',4);h[4]=('const',1)
        self.assertEqual(arguments(r,128,h)[:2],(('stack',-120),('const',1)))
        for v in (('reg',5),('stack',1),('stack',125)):
            bad=h.copy();bad[3]=v
            with self.assertRaises(ValueError):arguments(r,128,bad)
        bad=h.copy();bad[4]=('reg',5)
        with self.assertRaises(ValueError):arguments(r,128,bad)
    def test_classes(self):
        self.assertEqual(classify((0x88630000,0x98630000,0x2c030000,0x41820008,0x4e800020)),
                         {'load_1':1,'store_1':1,'cmp_imm':1,'bc_cr':1,'return':1})
if __name__=='__main__':unittest.main(verbosity=2)
