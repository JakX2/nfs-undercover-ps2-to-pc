#!/usr/bin/env python3
import unittest
from audit_formatter_partial_accesses import load_geometry,integer_shape,census
B=0x80001000;SP=-864;F=48
def d(op,rt,ra,imm=0):return (op<<26)|(rt<<21)|(ra<<16)|(imm&0xffff)
def x(xo,rt,ra,rb):return (31<<26)|(rt<<21)|(ra<<16)|(rb<<11)|(xo<<1)
class Tests(unittest.TestCase):
    def setUp(self):
        self.gp=[('const',0)]*32;self.gp[1]=('stack',SP-F)
    def test_load(self):
        self.assertEqual(load_geometry(d(32,3,1,8),self.gp),('stack',SP-40,4))
        self.gp[5]=('const',-4)
        self.assertEqual(load_geometry(x(23,3,1,5),self.gp),('stack',SP-52,4))
        self.gp[5]=('partial',())
        with self.assertRaisesRegex(ValueError,'load address'):load_geometry(x(23,3,1,5),self.gp)
        self.assertIsNone(load_geometry(d(36,3,1,8),self.gp))
    def test_integer(self):
        self.gp[3]=('partial',());self.gp[4]=('reg',4)
        self.assertEqual(integer_shape(x(104,5,3,0),self.gp),('neg',1,1,0))
        self.assertEqual(integer_shape(x(28,3,5,4),self.gp),('and',2,1,1))
        self.assertEqual(integer_shape(d(14,3,0,9),self.gp),('addi',0,0,0))
        self.assertEqual(integer_shape(x(824,3,5,8),self.gp),('srawi',1,1,0))
    def test_census(self):
        mem={SP-40:('byte',1),SP-39:('byte',2)}
        g=tuple(self.gp);loaded=list(g);loaded[3]=('partial',(('byte',1),('byte',2),('uninitialized',SP-38),('uninitialized',SP-37)))
        final={**mem,**{SP+16+i:c for i,c in enumerate(loaded[3][1])}}
        trace=((B,d(32,3,1,8),g,mem),(B+4,d(36,3,1,64),tuple(loaded),mem),(B+8,x(104,5,3,0),tuple(loaded),final))
        initial=list(g);initial[1]=('stack',SP)
        result,bound=census(trace,((B+4,SP+16,4,'partial'),),(B,initial,{},B-4,()),(0,0,(),F))
        self.assertEqual(result,((1,'load',4,'child',2,0,'partial',0),(2,'store',4,'caller_storage',0,4,'partial',1)))
        self.assertEqual(bound,('neg',1,1,0))
if __name__=='__main__':unittest.main(verbosity=2)
