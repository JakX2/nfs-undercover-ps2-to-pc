#!/usr/bin/env python3
import unittest
from prepare_formatter_caller_stack_move_contract import extend
from guarded_continuation import GUARD
P=0x80010000;N=0x60000000
def d(op,r,a,n):return (op<<26)|(r<<21)|(a<<16)|(n&0xffff)
def bc(bo,bi,n):return (16<<26)|(bo<<21)|(bi<<16)|(n&0xfffc)
def x_or(s,a,b,rc=0):return (31<<26)|(s<<21)|(a<<16)|(b<<11)|(444<<1)|rc
class StackMove(unittest.TestCase):
    def setUp(self):
        self.words=[N]*32
        self.words[5]=d(34,3,1,19);self.words[6]=d(11,0,3,0xa5)
        self.words[7]=bc(12,2,16);self.words[11]=x_or(1,4,1)
        self.words[12]=d(14,5,4,16)
        self.body=[N,GUARD,GUARD,GUARD,GUARD,self.words[5],self.words[6],GUARD]
        self.live=[('reg',r) for r in range(32)];self.live[1]=('stack',-704)
        self.initial=tuple(self.live);self.live[3]=('const',0xa5)
        self.cr=(None,)*32;self.guards=(P+4,P+8,P+12,P+16)
    def probe(self):
        byte=({P:tuple(self.body)},(P,P+20,self.words[5],19,0xa5,P+24,self.words[6]))
        return extend(byte,self.words,self.live,self.cr,0,self.guards,self.initial)
    def test_exact(self):
        (blocks,info),live,cr,guards=self.probe()
        self.assertEqual(info,(P,128,P+44,self.words[11],0,P+48,self.words[12]))
        self.assertEqual(live[4],('stack',-704));self.assertEqual(live[1],self.initial[1])
        self.assertEqual(cr[:4],(False,False,True,None))
        self.assertTrue(all(blocks[P][(a-P)//4]==GUARD for a in guards))
    def test_offset(self):
        self.words[11]=x_or(7,4,7);self.live[7]=('stack',-704+124)
        self.initial=tuple(self.live)
        (_,info),live,_,_=self.probe()
        self.assertEqual(info[4],124);self.assertEqual(live[4],('stack',-580))
    def test_outside_parent(self):
        for offset in (-4,704):
            self.words[11]=x_or(7,4,7);self.live[7]=('stack',-704+offset);self.initial=tuple(self.live)
            with self.assertRaisesRegex(ValueError,'range'):self.probe()
    def test_record(self):
        self.words[11]|=1
        with self.assertRaisesRegex(ValueError,'encoding'):self.probe()
    def test_distinct_inputs(self):
        self.words[11]=x_or(1,4,2)
        with self.assertRaisesRegex(ValueError,'encoding'):self.probe()
    def test_unknown_identity(self):
        self.words[11]=x_or(14,4,14)
        with self.assertRaisesRegex(ValueError,'provenance'):self.probe()
    def test_changed_stack(self):
        self.live[1]=('stack',-752)
        with self.assertRaisesRegex(ValueError,'frame'):self.probe()
    def test_inherited_guard(self):
        self.body.extend([GUARD]*5);self.guards+=(P+48,)
        with self.assertRaisesRegex(ValueError,'overlap'):self.probe()
    def test_nonvolatile(self):
        self.words[11]=x_or(1,16,1)
        with self.assertRaisesRegex(ValueError,'predecessor'):self.probe()
if __name__=='__main__':unittest.main(verbosity=2)
