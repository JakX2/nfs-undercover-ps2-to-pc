#!/usr/bin/env python3
import unittest
from audit_formatter_caller_integer import audit,after_byte
P=0x80010000;SP=-864;LOAD=0x88610013
def d(op,rt,ra,imm=0):return (op<<26)|(rt<<21)|(ra<<16)|(imm&0xffff)
class Integer(unittest.TestCase):
    def setUp(self):
        self.initial=[('reg',r) for r in range(32)];self.initial[1]=('stack',SP)
        self.gp=list(self.initial);self.gp[1]=('stack',SP-48)
        self.info=(P,P+8,LOAD,0x48000001,19,9,P+12,d(14,4,3,1))
    def probe(self,w):return audit(self.info[:-1]+(w,),self.gp,self.initial,0x80610010)
    def test_exact(self):
        gp,r=after_byte(self.info,self.gp,self.initial)
        self.assertEqual((r,gp[1],gp[3]),(3,('stack',SP),('const',9)))
        self.assertEqual(self.gp[3],('reg',3))
        self.assertEqual(self.probe(d(14,4,3,1)),(('add_immediate',1,1,1,0,0,0,0,0,0,0,0),1,0,0,'load'))
    def test_reserved(self):self.assertEqual(self.probe(d(14,1,3,0))[2:4],(1,0))
    def test_saved(self):self.assertEqual(self.probe(d(14,14,3,0))[2:4],(0,1))
    def test_unknown(self):self.assertEqual(self.probe(d(14,4,5,0))[0][6],1)
    def test_partial(self):
        self.gp[5]=('partial',())
        self.assertEqual(self.probe(d(14,4,5,0))[0][5],1)
    def test_bad_load(self):
        for w in (d(35,3,1,19),d(34,1,1,19),d(32,3,1,19)):
            with self.assertRaisesRegex(ValueError,'byte'):after_byte(self.info[:2]+(w,)+self.info[3:],self.gp,self.initial)
    def test_bad_stack(self):
        self.gp[1]=('stack',SP)
        with self.assertRaisesRegex(ValueError,'state'):after_byte(self.info,self.gp,self.initial)
    def test_non_integer(self):
        with self.assertRaisesRegex(ValueError,'family'):self.probe(0x80610010)
if __name__=='__main__':unittest.main(verbosity=2)
