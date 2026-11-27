#!/usr/bin/env python3
import unittest
from prepare_formatter_return_contract import contract
from guarded_continuation import GUARD
P=0x80010000;C=0x80020000;CALL=P+4;LR=P+8;RET=C+388
def bl(a,b):return 0x48000001|((b-a)&0x03fffffc)
class Return(unittest.TestCase):
    def setUp(self):
        self.call=bl(CALL,C);self.parent=(0x60000000,self.call,GUARD)
        self.words=[0x60000000,self.call,0x38630001]
        self.rows=tuple((C+4*i,0x60000000) for i in range(96))+((RET-4,0x38210030),)
        child=list(x[1] for x in self.rows)+[0x4e800020,GUARD]
        self.blocks={P:self.parent,C:tuple(child)}
        self.prior=({P:self.parent,C:(0x60000000,GUARD)},P,P,C,0x60000000,((CALL,self.call),),0xffff0000,())
        self.gp=[('reg',r) for r in range(32)];self.gp[3]=('const',7)
        self.fields=(C,LR,RET,0x4e800020,48,0,0)
    def probe(self):return contract((self.blocks,self.fields,self.rows,tuple(range(32)),(),()),self.prior,self.words,self.gp)
    def test_exact(self):self.assertEqual(self.probe(),(P,LR,GUARD,'integer','const'))
    def test_wrong_call(self):
        self.words[1]^=4
        with self.assertRaisesRegex(ValueError,'guard'):self.probe()
    def test_wrong_lr(self):
        self.fields=(C,LR+4,*self.fields[2:])
        with self.assertRaisesRegex(ValueError,'call identity'):self.probe()
    def test_changed_guard(self):
        self.blocks[P]=tuple(self.words)
        with self.assertRaisesRegex(ValueError,'guard'):self.probe()
    def test_original_guard(self):
        self.words[2]=GUARD
        with self.assertRaisesRegex(ValueError,'guard'):self.probe()
    def test_bad_ret(self):
        self.blocks[C]=self.blocks[C][:-2]+(0x60000000,GUARD)
        with self.assertRaisesRegex(ValueError,'epilogue'):self.probe()
    def test_other_return_value(self):
        self.gp[3]=('partial',())
        self.assertEqual(self.probe()[-1],'partial')
if __name__=='__main__':unittest.main(verbosity=2)
