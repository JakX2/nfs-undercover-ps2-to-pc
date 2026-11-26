#!/usr/bin/env python3
"""Source-only helper opcode shape regressions."""
import unittest
from prepare_ipc_dispatch_native import helper_shape
N=0x60000000
RET=0x4e800020
ST=0x90830000
LD=0x80630000
STX=(31<<26)|(151<<1)
LDX=(31<<26)|(23<<1)
class Shape(unittest.TestCase):
    def test_exact(self):
        for w,wr in ((ST,True),(LD,False),(STX,True),(LDX,False)):
            self.assertEqual(helper_shape((N,w,RET),wr),1)
    def test_refusals(self):
        for words,wr in (((N,RET),True),((LD,RET),True),((ST,ST,RET),True),
                        ((ST,0x48000001,RET),True),((ST,0x44000002,RET),True),
                        ((ST,37<<26,RET),True),((ST,N),True),((N,)*16+(RET,),False)):
            with self.subTest(words=words),self.assertRaises(ValueError):helper_shape(words,wr)
if __name__=='__main__':unittest.main(verbosity=2)
