#!/usr/bin/env python3
import unittest
from audit_formatter_caller_branch import condition_effect,branch
from prepare_formatter_caller_integer_contract import step
P=0x80010000
def d(op,r,a,n):return (op<<26)|(r<<21)|(a<<16)|(n&0xffff)
def bc(bo,bi,disp):return (16<<26)|(bo<<21)|(bi<<16)|(disp&0xfffc)
class Branch(unittest.TestCase):
    def setUp(self):
        self.g=[('reg',r) for r in range(32)];self.g[3]=('const',0xffffffff)
        self.cr=(None,)*32
    def test_compare(self):
        w=d(11,0,3,0);after,_=step(w,self.g)
        cr=condition_effect(w,self.g,after,self.cr)
        self.assertEqual(cr[:4],(True,False,False,None))
        self.assertEqual(branch(P+8,bc(12,0,16),cr,P,64),('conditional',False,True,False,P+24,P+24))
        self.assertEqual(branch(P+8,bc(4,0,16),cr,P,64)[2],False)
        self.assertIsNone(branch(P+8,bc(12,3,16),cr,P,64)[2])
    def test_unsigned(self):
        w=d(10,4,3,0);after,_=step(w,self.g)
        cr=condition_effect(w,self.g,after,self.cr)
        self.assertEqual(cr[4:8],(False,True,False,None));self.assertEqual(cr[:4],self.cr[:4])
    def test_record(self):
        w=d(28,3,4,0);after,_=step(w,self.g)
        self.assertEqual(condition_effect(w,self.g,after,self.cr)[:4],(False,False,True,None))
    def test_nonrecord(self):
        w=d(14,4,3,1);after,_=step(w,self.g)
        self.assertEqual(condition_effect(w,self.g,after,self.cr),self.cr)
    def test_counter(self):
        self.assertIsNone(branch(P+8,bc(0,0,16),self.cr,P,64)[2])
        cr=(True,)+self.cr[1:]
        self.assertEqual(branch(P+8,bc(0,0,16),cr,P,64)[:3],('conditional',True,False))
    def test_backedge(self):
        self.assertEqual(branch(P+16,bc(20,0,-8),self.cr,P,64),('conditional',False,True,True,P+8,P+8))
    def test_direct(self):
        self.assertEqual(branch(P+8,0x48000010,self.cr,P,64),('direct',False,True,False,P+24,P+24))
    def test_outside(self):
        self.assertEqual(branch(P+8,0x48000100,self.cr,P,64)[4:],(None,None))
    def test_link(self):
        self.assertEqual(branch(P+8,0x48000011,self.cr,P,64)[0],'unsupported')
    def test_geometry(self):
        with self.assertRaisesRegex(ValueError,'geometry'):branch(P+1,0x48000010,self.cr,P,64)
if __name__=='__main__':unittest.main(verbosity=2)
