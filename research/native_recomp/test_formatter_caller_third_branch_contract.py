#!/usr/bin/env python3
import unittest
from prepare_formatter_caller_third_branch_contract import extend
from guarded_continuation import GUARD
P=0x80010000;N=0x60000000;CMP=0x2c030009
def bc(bo,bi,d):return (16<<26)|(bo<<21)|(bi<<16)|(d&0xfffc)
class Third(unittest.TestCase):
    def setUp(self):
        self.words=[N]*24;self.words[2]=bc(12,0,20);self.words[3]=bc(12,1,24)
        self.words[9]=CMP;self.words[10]=bc(12,0,20)
        self.first=({},(P,96,P+8,self.words[2],False,P+12,self.words[3],P+28))
        self.second=({},(P,96,P+12,self.words[3],True,P+36,CMP,P+16))
        self.body=list(self.words[:4])+[GUARD]*5+[CMP,self.words[10],GUARD]
        self.post=({P:tuple(self.body)},((P+36,CMP,((3,9),)),),P+40,self.words[10])
        self.edge=('conditional',False,False,False,P+60,P+44)
    def probe(self):return extend(self.first,self.second,self.post,self.edge,self.words)
    def update_body(self):self.post=({P:tuple(self.body)},*self.post[1:])
    def test_exact(self):
        (blocks,info),reason,family=self.probe()
        self.assertEqual((reason,family,info[4:]),('admitted','integer',(False,P+44,N,P+60)))
        self.assertTrue(all(blocks[P][i]==GUARD for i in (4,7,15)))
    def test_alternate(self):
        self.body.extend([GUARD,GUARD,GUARD,N]);self.update_body()
        self.assertEqual(self.probe(),(None,'alternate_already_admitted','integer'))
    def test_chosen(self):
        self.body[11]=N;self.update_body()
        self.assertEqual(self.probe(),(None,'chosen_already_admitted','integer'))
    def test_guard(self):
        self.body[7]=N;self.update_body()
        with self.assertRaisesRegex(ValueError,'predecessor'):self.probe()
    def test_changed_edge(self):
        self.edge=self.edge[:4]+(P+64,P+44)
        with self.assertRaisesRegex(ValueError,'edge'):self.probe()
    def test_counter(self):
        self.edge=('conditional',True,*self.edge[2:])
        with self.assertRaisesRegex(ValueError,'edge'):self.probe()
    def test_disjoint(self):
        self.body.extend([GUARD]*5+[N]);self.update_body()
        (blocks,_),_,_=self.probe()
        self.assertEqual(blocks[P][17],N)
if __name__=='__main__':unittest.main(verbosity=2)
