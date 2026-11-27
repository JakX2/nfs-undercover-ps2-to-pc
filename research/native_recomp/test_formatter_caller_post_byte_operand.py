#!/usr/bin/env python3
import unittest
from audit_formatter_caller_post_byte_operand import audit
from guarded_continuation import GUARD
P=0x80010000;N=0x60000000
def d(op,r,a,n):return (op<<26)|(r<<21)|(a<<16)|(n&0xffff)
def bc(bo,bi,n):return (16<<26)|(bo<<21)|(bi<<16)|(n&0xfffc)
class Operand(unittest.TestCase):
    def setUp(self):
        self.words=[N]*32
        self.words[5]=d(34,3,1,19);self.words[6]=d(11,0,3,0xa5)
        self.words[7]=bc(12,2,16);self.words[11]=d(14,4,14,1)
        self.words[12]=d(32,5,1,16)
        self.body=[N,GUARD,GUARD,GUARD,GUARD,self.words[5],self.words[6],GUARD]
        self.initial=tuple(('reg',r) for r in range(32))
        self.live=list(self.initial);self.live[3]=('const',0xa5)
        self.cr=(None,)*32;self.guards=(P+4,P+8,P+12,P+16)
    def probe(self):
        byte=({P:tuple(self.body)},(P,P+20,self.words[5],19,0xa5,P+24,self.words[6]))
        return audit(byte,self.words,self.live,self.cr,1<<14,self.guards,self.initial)
    def test_identity(self):
        row,p,reserved,saved,protected,next_family=self.probe()
        self.assertEqual(row[:7],('add_immediate',1,1,0,0,0,1))
        self.assertEqual((p['identity'],p['same_entry'],p['entry_saved'],reserved,saved,protected,next_family),(1,1,1,0,0,0,'load'))
    def test_stack(self):
        self.live[14]=('stack',-704)
        row,p,*_=self.probe();self.assertEqual(row[4],1);self.assertEqual(p['identity'],0)
    def test_partial(self):
        self.live[14]=('partial',(('byte',1),('byte',2),('uninitialized',3),('uninitialized',4)))
        row,p,*_=self.probe();self.assertEqual((row[5],p['known_partial_bytes'],p['opaque_partial_bytes']),(1,2,2))
    def test_constant_continues(self):
        self.live[14]=('const',9)
        with self.assertRaisesRegex(ValueError,'predecessor'):self.probe()
    def test_unknown_origin(self):
        self.live[14]=('reg',32)
        with self.assertRaisesRegex(ValueError,'state'):self.probe()
    def test_reserved_effect(self):
        self.words[11]=d(14,1,14,1)
        with self.assertRaisesRegex(ValueError,'predecessor'):self.probe()
if __name__=='__main__':unittest.main(verbosity=2)
