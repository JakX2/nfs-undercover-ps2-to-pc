#!/usr/bin/env python3
import unittest
from analyze_formatter_nested_frontier import validate
from analyze_formatter_nested_path import nested
from prepare_post_stm_sc_report_formatter_path import const
R=0x80001000;T=0x80002000;L=0x80003000;A=0x80010000
def ins(op,r,a,v):return (op<<26)|(r<<21)|(a<<16)|(v&0xffff)
def bl(a,z):return 0x48000001|((z-a)&0x03fffffc)
class Tests(unittest.TestCase):
    def record(self):
        gp=[('reg',i) for i in range(32)];gp[1]=('stack',-128);gp[3]=const(A)
        state=((),{}, {},None,None,0,frozenset())
        ws=(ins(37,1,1,-48),0x7c0802a6,ins(36,0,1,52),ins(32,4,3,0),bl(R+16,T))
        missed=[]
        def refuse(a,n):raise ValueError('test unknown')
        with self.assertRaisesRegex(ValueError,'test unknown'):
            nested(R,ws,gp,{},state,(),L,read_resolver=refuse,read_refusal=lambda *x:missed.append(x))
        self.assertEqual(len(missed),1)
        return missed[0]
    def test_exact_boundary(self):
        record=self.record()
        self.assertEqual(record[2],(R,R+4,R+8,R+12))
        self.assertEqual(record[5][4],('reg',4))
        self.assertEqual(validate(record)[:3],(3,3,48))
        self.assertEqual(len(record[4]),2)
    def test_repeat_refused(self):
        record=list(self.record());record[2]=(R,R+12,R+8,R+12)
        with self.assertRaisesRegex(ValueError,'repeated'):validate(record)
    def test_prior_effect_refused(self):
        record=list(self.record());record[4]+=((R+12,'data_read',4,A),)
        with self.assertRaisesRegex(ValueError,'repeated'):validate(record)
if __name__=='__main__':unittest.main(verbosity=2)
