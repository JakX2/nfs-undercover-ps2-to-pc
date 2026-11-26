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
    def test_second_header(self):
        rows=tuple((R+4*i,N) for i in range(44))
        c=({},(R,L,R+176,0x80630000,48,A,4),rows,
           ((R,4,T,False,False),(R+140,4,T+4,False,False)),((4,32),),
           ((R,T,b'abcd'),(R+140,T+4,b'1234')))
        s=render(c)
        self.assertIn('IpcDispatchWord,44> path',s)
        self.assertIn('false,false,0x61626364u',s)
        self.assertIn('false,false,0x31323334u',s)
        self.assertIn('slots,{0x80040000u,0x00000004u}',s)
    def test_control_header(self):
        rows=tuple((R+4*i,N) for i in range(76))
        fields=(R,L,R+304,0x4e800420,48,0,0,R+400,N,383*4)
        c=({},fields,rows,(),((4,32),),())
        s=render(c)
        self.assertIn('IpcDispatchWord,76> path',s)
        self.assertIn('slots,{0x00000000u,0x00000000u},{0x80010190u,0x60000000u,0x000005fcu}',s)
        with self.assertRaisesRegex(ValueError,'control contract'):
            render(({},fields[:5]+(A,4)+fields[7:],rows,(),((4,32),),()))
    def test_expand(self):
        old={R:(N,GUARD),T:(N,)};new={**old,R:(N,N,GUARD)}
        self.assertEqual(expand(old,new,old,R),new)
        for blocks in ({**new,T:(GUARD,)},{**new,L:(N,)},old):
            with self.assertRaises(ValueError):expand(old,blocks,old,R)
        with self.assertRaises(ValueError):expand(old,new,{**old,R:(GUARD,)},R)
    def test_missing_const_read(self):
        c=({},(R,L,R+4,0x80630000,48,A,4),((R,N),),((R,4,A,False,False),),((4,32),),())
        with self.assertRaisesRegex(ValueError,'data contract'):render(c)
    def test_stack_read_not_a_file_constant(self):
        c=({},(R,L,R+4,0x80630000,48,A,4),((R,N),),((R,4,-8,True,False),),((4,32),),())
        self.assertIn('true,false}',render(c))
if __name__=='__main__':unittest.main(verbosity=2)
