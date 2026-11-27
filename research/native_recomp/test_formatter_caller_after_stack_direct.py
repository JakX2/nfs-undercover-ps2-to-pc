#!/usr/bin/env python3
import unittest
from audit_formatter_caller_after_stack_direct import audit
from guarded_continuation import GUARD
P=0x80010000;N=0x60000000;A=0x38600009
def b(pc,target,lk=0,aa=0):return (18<<26)|((target if aa else target-pc)&0x03fffffc)|(aa<<1)|lk
class Direct(unittest.TestCase):
    def probe(self,target,lk=0,aa=0,funcs=None):
        pc=P+8;w=b(pc,target,lk,aa)
        words=[N,A,w,N,N,N,N,N]
        blocks={P:(N,A,w,GUARD,GUARD)}
        rows=((P+4,A,(),pc,None,None),)
        return audit(P,32,(blocks,rows,pc,w),words,funcs or {})
    def test_local(self):
        x,d=self.probe(P+16);self.assertEqual((x[:7],d),((False,False,False,False,'local',1,0),P+16))
    def test_backward(self):
        x,d=self.probe(P);self.assertEqual((x[:7],d),((False,False,True,False,'local',0,1),P))
    def test_self(self):
        x,_=self.probe(P+8);self.assertTrue(x[3])
    def test_entry(self):
        x,d=self.probe(P+256,1,funcs={P+256:32});self.assertEqual((x[:7],d),((True,False,False,False,'function_entry',0,0),P+256))
    def test_interior(self):
        x,_=self.probe(P+260,funcs={P+256:32});self.assertEqual(x[4],'function_interior')
    def test_absolute(self):
        x,d=self.probe(0xff000000,aa=1);self.assertEqual(d,0xff000000);self.assertTrue(x[1])
    def test_unknown(self):
        x,_=self.probe(P+256);self.assertEqual(x[4],'unresolved')
    def test_bad_predecessor(self):
        with self.assertRaisesRegex(ValueError,'predecessor'):audit(P,8,({},(),P,N),[N,N],{})
if __name__=='__main__':unittest.main(verbosity=2)
