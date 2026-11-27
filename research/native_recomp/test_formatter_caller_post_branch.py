#!/usr/bin/env python3
import unittest
from audit_formatter_caller_post_branch import audit
from guarded_continuation import GUARD
P=0x80010000;SP=-864;N=0x60000000;LOAD=0x88610013;CALL=0x48000001
def d(op,r,a,n):return (op<<26)|(r<<21)|(a<<16)|(n&0xffff)
def bc(bo,bi,n):return (16<<26)|(bo<<21)|(bi<<16)|(n&0xfffc)
class PostBranch(unittest.TestCase):
    def setUp(self):
        self.initial=[('reg',r) for r in range(32)];self.initial[1]=('stack',SP)
        self.gp=list(self.initial);self.gp[1]=('stack',SP-48)
        self.a=d(14,4,3,1);self.c=d(11,0,4,0)
        self.b1=bc(12,0,16);self.b2=bc(12,1,24)
        self.words=[CALL,LOAD,self.a,self.c,self.b1,self.b2]+[N]*12
        self.words[11]=d(14,16,4,2);self.words[12]=d(14,5,16,3);self.words[13]=d(32,6,1,8)
        self.byte=({},(P,P+4,LOAD,CALL,19,9,P+8,self.a))
        self.integer=({},((P+8,self.a,((3,9),)),(P+12,self.c,((4,10),))),P+16,self.b1)
        b={P:tuple(self.words[:6])+(GUARD,)*6}
        self.first=(b,(P,len(self.words)*4,P+16,self.b1,False,P+20,self.b2,P+32))
        self.second=({P:b[P][:11]+(self.words[11],GUARD)},(P,len(self.words)*4,P+20,self.b2,True,P+44,self.words[11],P+24))
    def probe(self,**kw):return audit(self.byte,self.integer,self.first,self.second,self.gp,self.initial,self.words,1<<16,**kw)
    def test_exact(self):
        counts,inputs,saved,reason,family,name,kinds,cr=self.probe()
        self.assertEqual((dict(counts),inputs,saved,reason,family,cr),({'add_immediate':2},2,1,'caller integer opcode','load',3))
    def test_cap(self):
        x=self.probe(cap=1)
        self.assertEqual((sum(x[0].values()),x[3],x[4]),(1,'cap','integer'))
    def test_guard(self):
        b,info=self.first;v=list(b[P]);v[8]=N;self.first=({P:tuple(v)},info)
        with self.assertRaisesRegex(ValueError,'predecessor'):self.probe()
    def test_unknown(self):
        self.words[12]=d(14,5,6,3)
        x=self.probe();self.assertEqual((sum(x[0].values()),x[3],x[6]['reg']),(1,'caller integer inputs',1))
    def test_branch_outcome(self):
        b,info=self.second;self.second=(b,info[:4]+(False,)+info[5:])
        with self.assertRaisesRegex(ValueError,'predecessor'):self.probe()
if __name__=='__main__':unittest.main(verbosity=2)
