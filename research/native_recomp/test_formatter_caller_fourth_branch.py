#!/usr/bin/env python3
import unittest
from audit_formatter_caller_fourth_branch import audit
from test_formatter_caller_third_branch_contract import Third,P,N,CMP,bc
from guarded_continuation import GUARD
class Fourth(unittest.TestCase):
    def setUp(self):
        t=Third();t.setUp()
        self.first=t.first;self.second=t.second
        self.words=t.words;self.words[11]=bc(12,2,24)
        self.post=t.post
        rows,pc,w=self.post[1:]
        self.details=(rows,pc,w,(),(False,False,True,None)+(None,)*28,'caller integer opcode')
        b=list(t.body)+[GUARD]*4;b[11]=self.words[11]
        self.third=({P:tuple(b)},(P,96,pc,w,False,pc+4,self.words[11],P+60))
    def probe(self):return audit(self.first,self.second,self.post,self.third,self.words,self.details)
    def test_exact(self):self.assertEqual(self.probe(),('conditional',False,True,False,1,0,0,0,'integer',3))
    def test_unknown(self):
        self.details=self.details[:4]+((False,False,None,None)+(None,)*28,)+self.details[5:]
        self.assertEqual(self.probe()[2],None)
    def test_prior_guard(self):
        w=bc(12,2,16);self.words[11]=w
        b,info=self.third;v=list(b[P]);v[11]=w
        self.third=({P:tuple(v)},info[:6]+(w,info[-1]))
        self.assertEqual(self.probe()[5],1)
    def test_history(self):
        b,info=self.third;v=list(b[P]);v[0]^=1;self.third=({P:tuple(v)},info)
        with self.assertRaisesRegex(ValueError,'history'):self.probe()
    def test_changed_cr(self):
        self.details=self.details[:4]+((True,False,False,None)+(None,)*28,)+self.details[5:]
        with self.assertRaisesRegex(ValueError,'predecessor'):self.probe()
if __name__=='__main__':unittest.main(verbosity=2)
