#!/usr/bin/env python3
import unittest
from audit_formatter_partial_integer import classify,describe,special_destination
def d(op,rt,ra,imm=0):return (op<<26)|(rt<<21)|(ra<<16)|(imm&0xffff)
def x(xo,rt,ra,rb,rc=0):return (31<<26)|(rt<<21)|(ra<<16)|(rb<<11)|(xo<<1)|rc
class IntegerAudit(unittest.TestCase):
    def test_immediate(self):
        self.assertEqual(classify(d(14,3,0,4)),('add_immediate',(),(3,),0,0,0,0))
        self.assertEqual(classify(d(8,3,0,4)),('subtract_immediate_carry',(0,),(3,),0,0,1,0))
        self.assertEqual(classify(d(13,3,4,0)),('add_immediate_carry',(4,),(3,),1,0,1,0))
    def test_xo_overflow(self):
        self.assertEqual(classify(x(266+512,3,4,5,1)),('add',(4,5),(3,),1,0,1,1))
        self.assertEqual(classify(x(138,3,4,5)),('add_extended',(4,5),(3,),0,1,1,0))
        self.assertEqual(classify(x(104,3,4,0)),('negate',(4,),(3,),0,0,0,0))
    def test_x_not_xo(self):
        self.assertEqual(classify(x(536,3,4,5)),('shift_right',(3,5),(4,),0,0,0,0))
        self.assertEqual(classify(x(824,3,4,5,1)),('shift_arithmetic_immediate',(3,),(4,),1,0,1,0))
        self.assertEqual(classify(x(26,3,4,0)),('count_leading_zero',(3,),(4,),0,0,0,0))
    def test_provenance(self):
        g=[('reg',r) for r in range(32)];g[3]=('partial',());g[4]=('const',8);g[5]=('stack',-16)
        self.assertEqual(describe(x(444,3,3,4),g),('or',2,1,1,0,1,0,0,0,0,0,1))
        self.assertEqual(describe(x(266,6,4,5),g),('add',2,1,1,1,0,0,0,0,0,0,0))
        self.assertEqual(describe(x(444,3,4,3),g)[1],1)
    def test_special_destination(self):
        gp=[('reg',r) for r in range(32)];gp[3]=('const',0x80001000)
        self.assertEqual(special_destination(x(467,3,8,0),gp,0x80001000),('link',1,1))
        self.assertEqual(special_destination(x(467,3,8,0),gp,0x80002000),('link',1,0))
        self.assertEqual(special_destination(x(467,3,9,0),gp,0x80001000),('count',1,0))
        self.assertEqual(special_destination(x(467,4,1,0),gp,0x80001000),('xer',0,0))
        self.assertEqual(special_destination(x(467,3,8,0,1),gp,0x80001000),('not_special_write',0,0))
        self.assertEqual(special_destination(x(467,3,0,1),gp,0x80001000),('other',1,0))
    def test_unknown(self):
        self.assertEqual(classify(0),('unclassified',(),(),0,0,0,0))
        with self.assertRaisesRegex(ValueError,'geometry'):describe(0,[])
if __name__=='__main__':unittest.main(verbosity=2)
