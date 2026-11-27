#!/usr/bin/env python3
import unittest
from prepare_formatter_caller_integer_contract import step,extend
from guarded_continuation import GUARD
P=0x80010000;SP=-864;CALL=0x48000001;LOAD=0x88610013
def d(op,r,a,n):return (op<<26)|(r<<21)|(a<<16)|(n&0xffff)
def x(r,a,b,xo,rc=0):return (31<<26)|(r<<21)|(a<<16)|(b<<11)|(xo<<1)|rc
class CallerInteger(unittest.TestCase):
    def setUp(self):
        self.initial=[('reg',r) for r in range(32)];self.initial[1]=('stack',SP)
        self.gp=list(self.initial);self.gp[1]=('stack',SP-48)
        self.gp[3]=('const',0x80)
        self.first=x(3,4,0,954);self.second=d(14,5,4,1);self.stop=d(32,6,1,16)
        self.words=[CALL,LOAD,self.first,self.second,self.stop,0x60000000]
        self.blocks={P:(CALL,LOAD,self.first,GUARD)}
        self.info=(P,P+4,LOAD,CALL,19,128,P+8,self.first)
    def probe(self,**kwargs):return extend((self.blocks,self.info),self.words,self.gp,self.initial,**kwargs)
    def test_batch(self):
        c,reason=self.probe()
        self.assertEqual(reason,'caller integer opcode')
        self.assertEqual(c[1],((P+8,self.first,((3,128),)),(P+12,self.second,((4,0xffffff80),))))
        self.assertEqual(c[2:],(P+16,self.stop))
        self.assertEqual(c[0][P],tuple(self.words[:5])+(GUARD,))
    def test_cap(self):
        c,reason=self.probe(cap=1)
        self.assertEqual((len(c[1]),reason,c[2]),(1,'cap',P+12))
    def test_unknown(self):
        self.first=d(14,5,6,1);self.info=self.info[:-1]+(self.first,);self.words[2]=self.first;self.blocks[P]=(CALL,LOAD,self.first,GUARD)
        self.assertEqual(self.probe(),(None,'caller integer inputs'))
    def test_protected(self):
        with self.assertRaisesRegex(ValueError,'effects'):step(d(14,14,3,1),self.gp)
    def test_saved_parent(self):
        w=x(3,16,3,444)
        out,inputs=step(w,self.gp,saved_mask=1<<16)
        self.assertEqual((out[16],inputs),(('const',128),((3,128),)))
        for mask in (0,1<<17,(1<<16)|1):
            with self.assertRaisesRegex(ValueError,'effects'):step(w,self.gp,saved_mask=mask)
    def test_compare(self):
        out,inputs=step(d(11,0,3,0),self.gp)
        self.assertEqual(out,tuple(self.gp));self.assertEqual(inputs,((3,128),))
    def test_alias(self):
        out,inputs=step(x(3,5,3,444),self.gp)
        self.assertEqual(inputs,((3,128),));self.assertEqual(out[5],('const',128))
    def test_symbolic_stack_copy_is_explicitly_opt_in(self):
        word=x(1,10,1,444)
        self.gp[1]=('stack',-912)
        with self.assertRaisesRegex(ValueError,'inputs'):
            step(word,self.gp)
        out,inputs=step(word,self.gp,allow_stack_copy=True)
        self.assertEqual(inputs,())
        self.assertEqual(out[10],('stack',-912))
        self.assertEqual(out[1],self.gp[1])
        self.assertEqual(self.gp[10],('reg',10))

    def test_symbolic_copy_rejects_non_identity_and_record(self):
        self.gp[1]=('stack',-912)
        for word in (x(1,10,2,444),x(1,10,1,444,1),
                     x(1,10,1,316)):
            with self.subTest(word=word):
                with self.assertRaisesRegex(ValueError,'inputs'):
                    step(word,self.gp,allow_stack_copy=True)
        self.gp[1]=('stack',True)
        with self.assertRaisesRegex(ValueError,'inputs'):
            step(x(1,10,1,444),self.gp,allow_stack_copy=True)

    def test_wrap(self):
        self.gp[3]=('const',0xffffffff)
        self.assertEqual(step(d(14,5,3,1),self.gp)[0][5],('const',0))
    def test_reserved(self):
        for w in (x(3,5,1,954),d(11,1,3,0),x(0,3,3,32,1)):
            with self.assertRaisesRegex(ValueError,'encoding'):step(w,self.gp)
    def test_partial(self):
        self.gp[3]=('partial',())
        with self.assertRaisesRegex(ValueError,'inputs'):step(self.first,self.gp)
    def test_history(self):
        self.words[0]^=1
        with self.assertRaisesRegex(ValueError,'history'):self.probe()
if __name__=='__main__':unittest.main(verbosity=2)
