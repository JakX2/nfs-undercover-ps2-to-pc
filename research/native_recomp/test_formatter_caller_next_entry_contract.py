#!/usr/bin/env python3
import unittest
from prepare_formatter_caller_next_entry_contract import entry_contract
from guarded_continuation import GUARD
P=0x80010000;T=P-0x100;N=0x60000000;A=0x38600009;LOAD=0x80630000
def b(pc,target,lk=1):return (18<<26)|((target-pc)&0x03fffffc)|lk
class Entry(unittest.TestCase):
    def setUp(self):
        self.pc=P+8;self.w=b(self.pc,T);self.words=[N,A,self.w,N,N,N,N,N]
        self.blocks={P:(GUARD,A,self.w,GUARD,GUARD)}
        self.rows=((P+4,A,(),self.pc,None,None),);self.functions={P:32,T:16}
        self.live=[('reg',r) for r in range(32)];self.live[1]=('stack',-704)
        self.initial=tuple(self.live);self.guards=(P,);self.entry=(LOAD,N)
    def probe(self):
        return entry_contract(P,32,(self.blocks,self.rows,self.pc,self.w),self.words,self.functions,self.entry,self.live,self.initial,self.guards)
    def test_exact(self):
        blocks,info=self.probe()
        self.assertEqual(info,(P,32,self.pc,self.w,T,LOAD,P+12))
        self.assertEqual(blocks,{**self.blocks,T:(LOAD,GUARD)})
    def test_nonlink(self):
        self.w^=1;self.words[2]=self.w;self.blocks[P]=(GUARD,A,self.w,GUARD,GUARD)
        with self.assertRaisesRegex(ValueError,'geometry'):self.probe()
    def test_existing(self):
        self.blocks[T]=(LOAD,GUARD)
        with self.assertRaisesRegex(ValueError,'already present'):self.probe()
    def test_wrong_entry(self):
        self.entry=(N,N)
        with self.assertRaisesRegex(ValueError,'entry'):self.probe()
    def test_return(self):
        self.blocks[P]=(GUARD,A,self.w,N,GUARD)
        with self.assertRaisesRegex(ValueError,'return guard'):self.probe()
    def test_historical(self):
        self.blocks[P]=(N,A,self.w,GUARD,GUARD)
        with self.assertRaisesRegex(ValueError,'historical guard'):self.probe()
    def test_stack(self):
        self.live[1]=('stack',-752)
        with self.assertRaisesRegex(ValueError,'state'):self.probe()
    def test_unknown(self):
        del self.functions[T]
        with self.assertRaisesRegex(ValueError,'geometry'):self.probe()
if __name__=='__main__':unittest.main(verbosity=2)
