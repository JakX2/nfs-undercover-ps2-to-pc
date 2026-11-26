#!/usr/bin/env python3
import unittest
from prepare_post_stm_sc_report_dependency_abi import arguments,classify,memory_sites
B=0x80001000;A=0x80003000
class Abi(unittest.TestCase):
    def test_args(self):
        r=[('reg',i) for i in range(32)];r[4]=('stack',-120);r[13]=('const',A)
        h=[('reg',i) for i in range(32)];h[3]=('reg',4);h[4]=('const',1)
        self.assertEqual(arguments(r,128,h)[:2],(('stack',-120),('const',1)))
        h[3]=('expr',(('reg',13),-4))
        self.assertEqual(arguments(r,128,h)[:2],(('const',A-4),('const',1)))
        h[3]=('stack',-32)
        self.assertEqual(arguments(r,128,h)[0],('stack',-160))
    def test_classes(self):
        self.assertEqual(classify((0x88630000,0x98630000,0x2c030000,0x41820008,0x4e800020)),
                         {'load_1':1,'store_1':1,'cmp_imm':1,'bc_cr':1,'return':1})
    def test_sites(self):
        words=(0x88630000,0x98630000,0x90630004)
        self.assertEqual(memory_sites(B,words,A),((B,A,1,False),(B+4,A,1,True),(B+8,A+4,4,True)))
        for bad in ((0x88640000,*words[1:]),(*words[:2],0x90630001),words[:-1]):
            with self.assertRaises(ValueError):memory_sites(B,bad,A)
if __name__=='__main__':unittest.main(verbosity=2)
