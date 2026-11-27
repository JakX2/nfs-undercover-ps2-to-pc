#!/usr/bin/env python3
import unittest
from prepare_formatter_caller_byte_contract import extend
from guarded_continuation import GUARD
P=0x80010000;C=0x80020000;LR=P+8;SP=-864;CALL=0x4800fffd;LOAD=0x88610013;NEXT=0x60000000
class Byte(unittest.TestCase):
    def setUp(self):
        self.words=[0x60000000,CALL,LOAD,NEXT,0x60000000]
        self.blocks={P:(self.words[0],CALL,LOAD,GUARD),C:(0x4e800020,GUARD)}
        self.info=(P,LR,LOAD,CALL)
        self.initial=[('reg',r) for r in range(32)];self.initial[1]=('stack',SP)
        self.gp=list(self.initial);self.gp[1]=('stack',SP-48)
        self.parent={SP+8:('byte',1)};self.mem=dict(self.parent)
        self.mem.update({SP+16+i:('byte',9 if i==3 else 0) for i in range(4)})
        self.admitted=((C,SP+16,4,'const'),)
    def probe(self):return extend((self.blocks,self.info),self.words,self.gp,self.mem,self.initial,self.parent,self.admitted)
    def test_exact(self):
        blocks,info=self.probe()
        self.assertEqual(info,(P,LR,LOAD,CALL,19,9,LR+4,NEXT))
        self.assertEqual(blocks[P],(self.words[0],CALL,LOAD,NEXT,GUARD))
    def test_opaque(self):
        self.mem[SP+19]=('uninitialized',SP-38)
        with self.assertRaisesRegex(ValueError,'provenance'):self.probe()
    def test_no_output(self):
        self.admitted=()
        with self.assertRaisesRegex(ValueError,'provenance'):self.probe()
    def test_missing(self):
        del self.mem[SP+19]
        with self.assertRaisesRegex(ValueError,'provenance'):self.probe()
    def test_inherited(self):
        self.parent[SP+19]=self.mem[SP+19]
        with self.assertRaisesRegex(ValueError,'provenance'):self.probe()
    def test_guard(self):
        self.words[3]=GUARD
        with self.assertRaisesRegex(ValueError,'boundary'):self.probe()
    def test_history(self):
        self.words[0]^=1
        with self.assertRaisesRegex(ValueError,'history'):self.probe()
    def test_overlap(self):
        self.blocks[P]+=(NEXT,)
        with self.assertRaisesRegex(ValueError,'overlap'):self.probe()
if __name__=='__main__':unittest.main(verbosity=2)
