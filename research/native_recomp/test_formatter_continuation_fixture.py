#!/usr/bin/env python3
import unittest
from prepare_formatter_continuation_fixture import render,trace_entry,updated_leaf
from guarded_continuation import GUARD
R=0x80001000;T=0x80002000;L=0x80003000;N=0x60000000
class Test(unittest.TestCase):
    def setUp(self):
        self.p=({},R,R+4,T,N,((R+4,N),),1<<14,((3,'stack',-864),(4,'const',7)))
    def test_header(self):
        s=render(self.p)
        self.assertIn('RegisterContinuationArgument{3u,0,true}',s)
        self.assertIn('RegisterContinuationArgument{4u,7,false}',s)
        self.assertIn('RegisterContinuationSpec expected',s)
    def test_trace(self):
        s='loc_80001004: ;\n    // 0x80001004: 60000000\n    ++ctx.inst_count;\n    formatter_continuation_before(ctx,0x80001004u,0x60000000u);\n'
        result=trace_entry(s,R+4,N)
        self.assertLess(result.index('trace_call'),result.index('++ctx.inst_count'))
        with self.assertRaises(ValueError):trace_entry(result,R+4,N)
    def test_link(self):
        prior=(None,None,None,(L,R+4,GUARD),(N,),(L,),(L,False,T,1,b'x'),1)
        self.assertIn('0x80003000u,0x80001004u,0x60000000u',updated_leaf(prior,self.p))
        with self.assertRaises(ValueError):updated_leaf((*prior[:3],(L,R+8,GUARD),*prior[4:]),self.p)
if __name__=='__main__':unittest.main(verbosity=2)
