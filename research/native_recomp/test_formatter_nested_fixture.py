#!/usr/bin/env python3
import unittest
from prepare_formatter_nested_fixture import render,expand
from guarded_continuation import GUARD
R=0x80010000;T=0x80020000;L=0x80030000;A=0x80040000;N=0x60000000
class Test(unittest.TestCase):
    def test_header(self):
        c=({},(R,L,R+4,0x80630000,48,A,4),((R,N),),((R,4,A,False,False),),((4,32),),((R,A,b'abcd'),))
        s=render(c)
        self.assertIn('false,false,0x61626364u',s)
        self.assertIn('slots,{0x80040000u,0x00000004u}',s)
    def test_expand(self):
        old={R:(N,GUARD),T:(N,)};new={**old,R:(N,N,GUARD)}
        self.assertEqual(expand(old,new,old,R),new)
        for blocks in ({**new,T:(GUARD,)},{**new,L:(N,)},old):
            with self.assertRaises(ValueError):expand(old,blocks,old,R)
        with self.assertRaises(ValueError):expand(old,new,{**old,R:(GUARD,)},R)
if __name__=='__main__':unittest.main(verbosity=2)
