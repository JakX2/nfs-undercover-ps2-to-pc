#!/usr/bin/env python3
import unittest
from test_formatter_caller_post_branch import PostBranch,P,N,d,bc
from prepare_formatter_caller_post_integer_contract import extend
from guarded_continuation import GUARD
class Contract(PostBranch):
    def contract(self):
        return extend(self.byte,self.integer,self.first,self.second,self.gp,self.initial,self.words,1<<16)
    def test_contract(self):
        (blocks,rows,end,w),_,_=self.contract()
        self.assertEqual((len(rows),end,w),(2,P+52,self.words[13]))
        self.assertEqual(blocks[P][8],GUARD)
        self.assertEqual(blocks[P][6],GUARD)
        self.assertEqual(blocks[P][12:15],(self.words[12],self.words[13],GUARD))
    def test_overlap(self):
        b,info=self.second;self.second=({P:b[P][:12]+(self.words[12],)},info)
        with self.assertRaisesRegex(ValueError,'overlap'):self.contract()
    def test_disjoint(self):
        b,info=self.second;self.second=({P:b[P]+(GUARD,GUARD,self.words[15])},info)
        (blocks,*_),_,_=self.contract()
        self.assertEqual(blocks[P][15],self.words[15])
    def test_history(self):
        b,info=self.second;self.second=({P:b[P]+(GUARD,GUARD,N^1)},info)
        with self.assertRaisesRegex(ValueError,'history'):self.contract()
if __name__=='__main__':unittest.main(verbosity=2)
