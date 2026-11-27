#!/usr/bin/env python3
import unittest
from audit_formatter_caller_after_stack_move import stack_step,extend,LIMIT
from guarded_continuation import GUARD
P=0x80010000;N=0x60000000
def d(op,r,a,n):return (op<<26)|(r<<21)|(a<<16)|(n&0xffff)
def x_or(s,a,b,rc=0):return (31<<26)|(s<<21)|(a<<16)|(b<<11)|(444<<1)|rc
def bc(bo,bi,n):return (16<<26)|(bo<<21)|(bi<<16)|(n&0xfffc)
class Relative(unittest.TestCase):
    def setUp(self):
        self.gp=[('reg',r) for r in range(32)];self.gp[1]=('stack',-704)
        self.gp[3]=self.gp[4]=('stack',160);self.gp[5]=('const',9)
    def step(self,w):return stack_step(w,self.gp,parent=-704)
    def test_add(self):
        gp,proof=self.step(d(14,6,3,-12))
        self.assertEqual(gp[6],('stack',148));self.assertEqual(proof,((3,('stack',864)),))
    def test_alias(self):
        gp,proof=self.step(d(14,3,3,4))
        self.assertEqual(gp[3],('stack',164));self.assertEqual(self.gp[3],('stack',160))
    def test_copy(self):
        gp,proof=self.step(x_or(3,6,3));self.assertEqual(gp[6],self.gp[3])
    def test_constant(self):
        gp,proof=self.step(d(14,6,5,4));self.assertEqual((gp[6],proof),(('const',13),((5,9),)))
    def test_record(self):
        with self.assertRaisesRegex(ValueError,'opcode'):self.step(x_or(3,6,3,1))
    def test_distinct(self):
        with self.assertRaisesRegex(ValueError,'opcode'):self.step(x_or(3,6,4))
    def test_compare(self):
        with self.assertRaisesRegex(ValueError,'opcode'):self.step(d(11,0,3,0))
    def test_reserved(self):
        with self.assertRaisesRegex(ValueError,'effects'):self.step(d(14,1,3,4))
    def test_range(self):
        self.gp[3]=('stack',-704+LIMIT-1)
        with self.assertRaisesRegex(ValueError,'range'):self.step(d(14,6,3,1))
    def test_unknown(self):
        with self.assertRaisesRegex(ValueError,'provenance'):self.step(d(14,6,7,1))
    def test_mixed(self):
        words=[N]*32;words[5]=x_or(3,4,3);words[6]=d(14,6,4,4)
        words[7]=d(11,0,5,9);words[8]=bc(12,2,16);words[12]=d(32,7,6,0)
        body=(N,GUARD,GUARD,GUARD,GUARD,words[5],words[6],GUARD)
        move=({P:body},(P,128,P+20,words[5],864,P+24,words[6]))
        (blocks,rows,pc,w),reason,gp,cr=extend(move,words,self.gp,(None,)*32,0,(P+4,P+8,P+12,P+16))
        self.assertEqual((len(rows),pc,w,reason,gp[6]),(3,P+48,words[12],'caller integer opcode',('stack',164)))
        self.assertEqual(rows[0][2],((4,('stack',864)),))
        self.assertTrue(all(blocks[P][i]==GUARD for i in (1,2,3,4,9)))
if __name__=='__main__':unittest.main(verbosity=2)
