#!/usr/bin/env python3
import unittest
from prepare_post_stm_sc_report_dependency_path import execute,rotate,bitmask
B=0x80001000;A=0x80003000
class Path(unittest.TestCase):
    def test_paths(self):
        ws=(0x2c040000,0x41820010,0x80a30000,0x38a50001,0x90a30004,0x38600000,0x4e800020)
        sites=((B+8,A,4,False),(B+16,A+4,4,True));initial=bytes.fromhex('1234567800000000')
        self.assertEqual(execute(B,ws,(A,0),(A,8),sites,initial),(4,0,0,0,initial))
        self.assertEqual(execute(B,ws,(A,1),(A,8),sites,initial),(7,1,1,0,bytes.fromhex('1234567812345679')))
        for bad in ((0x2c050000,*ws[1:]),(*ws[:2],0x80a30004,*ws[3:]),(*ws[:4],0x90a30000,*ws[5:])):
            with self.assertRaises(ValueError):execute(B,bad,(A,1),(A,8),sites,initial)
    def test_masks(self):
        self.assertEqual(rotate(0x12345678,8),0x34567812)
        self.assertEqual(bitmask(24,31),0xff)
        self.assertEqual(bitmask(28,3),0xf000000f)
if __name__=='__main__':unittest.main(verbosity=2)
