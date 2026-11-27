#!/usr/bin/env python3
import unittest
from prepare_formatter_caller_mixed_byte_contract import extend
from guarded_continuation import GUARD
P=0x80010000;SP=-864;N=0x60000000
def d(op,r,a,n):return (op<<26)|(r<<21)|(a<<16)|(n&0xffff)
def bc(bo,bi,n):return (16<<26)|(bo<<21)|(bi<<16)|(n&0xfffc)
class MixedByte(unittest.TestCase):
    def setUp(self):
        self.words=[N]*32
        self.words[5]=d(11,0,3,9);self.words[6]=bc(12,2,12)
        self.words[9]=d(11,0,3,10);self.words[10]=bc(12,2,24)
        self.words[11]=bc(12,2,12)
        self.words[14]=d(34,3,1,19);self.words[15]=d(14,4,3,1)
        self.rows=((P+20,self.words[5],(),P+24,None,None),
                   (P+24,self.words[6],(),P+36,P+28,True),
                   (P+36,self.words[9],(),P+40,None,None),
                   (P+40,self.words[10],(),P+44,P+64,False),
                   (P+44,self.words[11],(),P+56,P+48,True))
        self.body=[GUARD]*19
        for i in (0,5,6,9,10,11,14):self.body[i]=self.words[i]
        self.live=[('reg',r) for r in range(32)];self.live[1]=('stack',SP)
        self.initial=tuple(self.live);self.mem={SP+19:('byte',0xa5)}
        self.parent={};self.admitted=((P+4,SP+16,4,'const'),);self.guards=(P+4,P+8,P+12,P+16)
    def probe(self):return extend(({P:tuple(self.body)},self.rows,P+56,self.words[14]),P,self.words,self.live,self.mem,self.initial,self.parent,self.admitted,self.guards)
    def test_exact(self):
        blocks,info=self.probe()
        self.assertEqual(info,(P,P+56,self.words[14],19,0xa5,P+60,self.words[15]))
        self.assertEqual(blocks[P][15:17],(self.words[15],GUARD))
        self.assertEqual([i for i,(a,b) in enumerate(zip(self.body,blocks[P])) if a!=b],[15])
    def test_opaque(self):
        self.mem[SP+19]=('uninitialized',SP+19)
        with self.assertRaisesRegex(ValueError,'provenance'):self.probe()
    def test_missing(self):
        self.mem.clear()
        with self.assertRaisesRegex(ValueError,'provenance'):self.probe()
    def test_inherited(self):
        self.parent=dict(self.mem)
        with self.assertRaisesRegex(ValueError,'provenance'):self.probe()
    def test_nonvolatile(self):
        self.words[14]=self.body[14]=d(34,15,1,19)
        with self.assertRaisesRegex(ValueError,'provenance'):self.probe()
    def test_update(self):
        self.words[14]=self.body[14]=d(35,3,1,19)
        with self.assertRaisesRegex(ValueError,'provenance'):self.probe()
    def test_history(self):
        self.body[0]^=1
        with self.assertRaisesRegex(ValueError,'history'):self.probe()
    def test_earlier_alternate(self):
        self.guards+=(P+60,)
        with self.assertRaisesRegex(ValueError,'overlap'):self.probe()
    def test_guard_tamper(self):
        self.body[7]=self.words[7]
        with self.assertRaisesRegex(ValueError,'guard'):self.probe()
    def test_next_occupied(self):
        self.body[15]=self.words[15]
        with self.assertRaisesRegex(ValueError,'overlap'):self.probe()
    def test_following_occupied(self):
        self.body[16]=self.words[16]
        with self.assertRaisesRegex(ValueError,'guard|overlap'):self.probe()
    def test_released_stack(self):
        self.live[1]=('stack',SP-48)
        with self.assertRaisesRegex(ValueError,'state'):self.probe()
if __name__=='__main__':unittest.main(verbosity=2)
