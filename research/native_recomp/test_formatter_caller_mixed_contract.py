#!/usr/bin/env python3
import unittest
from prepare_formatter_caller_mixed_contract import extend
from guarded_continuation import GUARD
P=0x80010000;N=0x60000000
def d(op,r,a,n):return (op<<26)|(r<<21)|(a<<16)|(n&0xffff)
def bc(bo,bi,n):return (16<<26)|(bo<<21)|(bi<<16)|(n&0xfffc)
class Mixed(unittest.TestCase):
    def setUp(self):
        self.words=[N]*32
        self.words[5]=d(14,4,3,1)
        self.words[6]=d(11,0,4,10)
        self.words[7]=bc(12,2,16)
        self.words[11]=d(14,5,4,2)
        self.words[12]=d(32,6,1,16)
        self.body=[N,GUARD,N,GUARD,N,self.words[5],GUARD]
        self.info=(P,128,P+16,N,False,P+20,self.words[5],P+4)
        self.gp=[('reg',r) for r in range(32)];self.gp[3]=('const',9)
        self.cr=(None,)*32
    def probe(self,**kw):return extend(({P:tuple(self.body)},self.info),self.words,self.gp,self.cr,0,(P+12,),**kw)
    def test_exact(self):
        (blocks,rows,pc,w),reason,gp,cr=self.probe()
        self.assertEqual((len(rows),pc,w,reason,gp[5]),(4,P+48,self.words[12],'caller integer opcode',('const',12)))
        self.assertEqual(rows[2][3:],(P+44,P+32,True))
        self.assertTrue(all(blocks[P][i]==GUARD for i in (1,3,8)))
        self.assertEqual(cr[:4],(False,False,True,None))
    def test_cap(self):
        (_,rows,pc,_),reason,_,_=self.probe(cap=2)
        self.assertEqual((len(rows),pc,reason),(2,P+28,'cap'))
    def test_unknown_cr(self):
        self.words[7]=bc(12,3,16)
        (_,rows,pc,_),reason,_,_=self.probe()
        self.assertEqual((len(rows),pc,reason),(2,P+28,'branch provenance'))
    def test_history(self):
        self.body[2]^=1
        with self.assertRaisesRegex(ValueError,'history'):self.probe()
    def test_chosen_conflict(self):
        self.body.extend([GUARD]*4+[self.words[11]])
        (_,rows,pc,_),reason,_,_=self.probe()
        self.assertEqual((len(rows),pc,reason),(2,P+28,'next label conflict'))
    def test_alternate_conflict(self):
        self.body.extend([GUARD,self.words[8]])
        (_,rows,pc,_),reason,_,_=self.probe()
        self.assertEqual((len(rows),pc,reason),(2,P+28,'branch alternate'))
    def test_disjoint(self):
        self.body.extend([GUARD]*13+[N])
        (blocks,_,_,_),_,_,_=self.probe()
        self.assertEqual(blocks[P][20],N)
    def test_unknown_input(self):
        self.gp[3]=('reg',3)
        (_,rows,pc,_),reason,_,_=self.probe()
        self.assertEqual((len(rows),pc,reason),(0,P+20,'caller integer inputs'))
if __name__=='__main__':unittest.main(verbosity=2)
