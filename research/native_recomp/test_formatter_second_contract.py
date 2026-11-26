#!/usr/bin/env python3
import unittest
from prepare_formatter_second_contract import compare
from guarded_continuation import GUARD
R=0x80010000;A=0x80020000;B=0x80030000;L=0x80040000;N=0x60000000;W=0x80630000
class Test(unittest.TestCase):
    def setUp(self):
        rows=tuple((R+4*i,N) for i in range(35))
        fields=(R,L,R+140,W,48,A,4)
        access=tuple((R+4*i,1,-48+i,True,True) for i in range(12))+((R+48,4,B,False,False),)
        slots=((4,32),);known=((R+48,B,b'abcd'),)
        self.old=({R:(N,)*35+(W,GUARD)},fields,rows,access,slots,known)
        self.cell=(A,b'1234')
        self.new=[{R:(N,)*35+(W,)+(N,)*9+(GUARD,)},(R,L,R+176,W,48,B,4),rows+(fields[2:4],)+tuple((R+4*i,N) for i in range(36,44)),access+((R+140,4,A,False,False),),slots,known+((R+140,A,b'1234'),)]
    def test_exact(self):self.assertEqual(compare(self.old,self.new,self.cell),self.new)
    def test_prefix(self):
        self.new[2]=self.new[2][1:]+((R,N),)
        with self.assertRaisesRegex(ValueError,'prefix'):compare(self.old,self.new,self.cell)
    def test_candidate(self):
        with self.assertRaisesRegex(ValueError,'candidate'):compare(self.old,self.new,(A,b'xxxx'))
    def test_slots(self):
        self.new[4]+=((-4,31),)
        with self.assertRaisesRegex(ValueError,'slots'):compare(self.old,self.new,self.cell)
    def test_word(self):
        self.new[0][R]=(W,)+self.new[0][R][1:]
        with self.assertRaisesRegex(ValueError,'old words'):compare(self.old,self.new,self.cell)
if __name__=='__main__':unittest.main(verbosity=2)
