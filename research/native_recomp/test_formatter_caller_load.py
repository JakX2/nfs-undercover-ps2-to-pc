#!/usr/bin/env python3
import unittest
from audit_formatter_caller_load import audit,audit_live
SP=-864
def d(op,rt,ra,imm=0):return (op<<26)|(rt<<21)|(ra<<16)|(imm&0xffff)
class CallerLoad(unittest.TestCase):
    def setUp(self):
        self.initial=[('reg',r) for r in range(32)];self.initial[1]=('stack',SP)
        self.gp=list(self.initial);self.gp[1]=('stack',SP-48)
        self.parent={SP+8+i:('byte',i) for i in range(4)}
        self.mem=dict(self.parent);self.mem.update({SP+16+i:('byte',i+10) for i in range(4)})
        self.admitted=((0x80010000,SP+16,4,'const'),)
    def probe(self,w,**kwargs):return audit(w,self.gp,self.mem,self.initial,self.parent,self.admitted,**kwargs)
    def test_inherited(self):self.assertEqual(self.probe(d(32,3,1,8)),('parent',4,4,0,4,0,'const','volatile',0))
    def test_output(self):self.assertEqual(self.probe(d(32,14,1,16)),('parent',4,0,4,4,0,'const','nonvolatile',0))
    def test_partial(self):
        self.mem[SP+18]=('uninitialized',SP-38);self.mem[SP+19]=('uninitialized',SP-37)
        self.assertEqual(self.probe(d(32,3,1,16)),('parent',4,0,4,4,2,'partial','volatile',0))
    def test_unwritten(self):self.assertEqual(self.probe(d(32,3,1,20)),('parent',4,0,0,0,0,'unknown','volatile',0))
    def test_released_child(self):
        self.mem[SP-4]=('byte',1)
        self.assertEqual(self.probe(d(32,3,1,-4))[0:2],('released_child',4))
    def test_outside(self):self.assertEqual(self.probe(d(32,3,1,704))[0],'outside_parent')
    def test_absolute(self):
        self.gp[4]=('const',0x80001000)
        self.assertEqual(self.probe(d(32,3,4),section=lambda a,n:'readonly',resolve=lambda a,n:b'abcd'),('readonly',4,0,0,4,0,'const','volatile',0))
        self.assertEqual(self.probe(d(32,3,4),section=lambda a,n:'writable',resolve=lambda a,n:b'abcd')[6],'unknown')
    def test_unresolved(self):self.assertEqual(self.probe(d(32,3,4))[0],'unresolved')
    def test_modified_parent(self):
        self.mem[SP+8]=('byte',9)
        with self.assertRaisesRegex(ValueError,'state'):self.probe(d(32,3,1,8))
class LiveState(unittest.TestCase):
    def test_post_release(self):
        gp=[('reg',r) for r in range(32)];gp[1]=('stack',-864)
        initial=tuple(gp);gp[3]=('stack',-848);mem={-848:('byte',9)}
        word=(34<<26)|(4<<21)|(3<<16)
        self.assertEqual(audit_live(word,gp,mem,initial,{},((0,-848,1,'const'),)),('parent',1,0,1,1,0,'const','volatile',0))
        gp[1]=('stack',-912)
        with self.assertRaisesRegex(ValueError,'state'):audit_live(word,gp,mem,initial,{},())
if __name__=='__main__':unittest.main(verbosity=2)
