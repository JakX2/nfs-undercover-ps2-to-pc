#!/usr/bin/env python3
import unittest
from audit_formatter_caller_after_mixed_byte import extend
from guarded_continuation import GUARD
P=0x80010000;N=0x60000000
def d(op,r,a,n):return (op<<26)|(r<<21)|(a<<16)|(n&0xffff)
def bc(bo,bi,n):return (16<<26)|(bo<<21)|(bi<<16)|(n&0xfffc)
class AfterByte(unittest.TestCase):
    def setUp(self):
        self.words=[N]*32
        self.words[5]=d(34,3,1,19);self.words[6]=d(11,0,3,0xa5)
        self.words[7]=bc(12,2,16);self.words[11]=d(14,4,3,1)
        self.words[12]=d(32,5,1,16)
        self.body=[N,GUARD,GUARD,GUARD,GUARD,self.words[5],self.words[6],GUARD]
        self.live=[('reg',r) for r in range(32)];self.live[3]=('const',0xa5)
        self.cr=(None,)*32;self.guards=(P+4,P+8,P+12,P+16)
    def probe(self,**kw):
        byte=({P:tuple(self.body)},(P,P+20,self.words[5],19,0xa5,P+24,self.words[6]))
        return extend(byte,self.words,self.live,self.cr,0,self.guards,**kw)
    def test_exact(self):
        (blocks,rows,pc,w),reason,live,_=self.probe()
        self.assertEqual((len(rows),pc,w,reason,live[4]),(3,P+48,self.words[12],'caller integer opcode',('const',0xa6)))
        self.assertEqual(rows[1][3:],(P+44,P+32,True))
        self.assertTrue(all(blocks[P][i]==GUARD for i in (1,2,3,4,8)))
    def test_wrong_load_effect(self):
        self.live[3]=('const',0)
        with self.assertRaisesRegex(ValueError,'state'):self.probe()
    def test_guard_tamper(self):
        self.body[2]=N
        with self.assertRaisesRegex(ValueError,'predecessor'):self.probe()
    def test_existing_guard(self):
        self.body.extend([GUARD]*4);self.guards+=(P+44,)
        (_,rows,pc,_),reason,_,_=self.probe()
        self.assertEqual((len(rows),pc,reason),(1,P+28,'next label conflict'))
    def test_cap(self):
        (_,rows,pc,_),reason,_,_=self.probe(cap=1)
        self.assertEqual((len(rows),pc,reason),(1,P+28,'cap'))
if __name__=='__main__':unittest.main(verbosity=2)
