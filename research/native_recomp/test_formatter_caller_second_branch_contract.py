#!/usr/bin/env python3
import unittest
from prepare_formatter_caller_second_branch_contract import extend
from guarded_continuation import GUARD
P=0x80010000;N=0x60000000
def bc(bo,bi,d):return (16<<26)|(bo<<21)|(bi<<16)|(d&0xfffc)
class Second(unittest.TestCase):
    def setUp(self):
        self.words=[N]*16;self.first_pc=P+8;self.pc=P+12;self.w=bc(12,1,24)
        self.words[2]=bc(12,0,20);self.words[3]=self.w
        self.first_other=P+28;self.chosen=P+36
        self.blocks={P:tuple(self.words[:4])+(GUARD,)*4}
        self.info=(P,64,self.first_pc,self.words[2],False,self.pc,self.w,self.first_other)
        self.second=('conditional',False,True,False,self.chosen,self.chosen)
    def probe(self):return extend((self.blocks,self.info),self.second,self.words)
    def test_exact(self):
        c,reason,family=self.probe()
        self.assertEqual((reason,family),('admitted','integer'))
        self.assertEqual(c[0][P][7],GUARD);self.assertEqual(c[0][P][4],GUARD)
        self.assertEqual(c[0][P][9],N)
    def test_shared_guard(self):
        self.second=self.second[:4]+(self.first_other,self.first_other)
        self.assertEqual(self.probe(),(None,'shared_first_guard','integer'))
    def test_existing_chosen(self):
        self.blocks[P]+=(GUARD,N)
        self.assertEqual(self.probe(),(None,'chosen_already_admitted','integer'))
    def test_existing_alternate(self):
        self.blocks[P]=self.blocks[P][:4]+(N,)+self.blocks[P][5:]
        self.assertEqual(self.probe(),(None,'alternate_already_admitted','integer'))
    def test_history(self):
        self.words[0]^=1
        with self.assertRaisesRegex(ValueError,'history'):self.probe()
    def test_counter(self):
        self.second=('conditional',True,*self.second[2:])
        with self.assertRaisesRegex(ValueError,'edge'):self.probe()
    def test_fallthrough(self):
        self.second=('conditional',False,False,False,self.chosen,self.pc+4)
        with self.assertRaisesRegex(ValueError,'edge'):self.probe()
if __name__=='__main__':raise SystemExit(unittest.main(verbosity=2))
