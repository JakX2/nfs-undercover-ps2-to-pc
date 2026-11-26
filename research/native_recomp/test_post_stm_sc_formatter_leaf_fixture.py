#!/usr/bin/env python3
import unittest
from prepare_post_stm_sc_formatter_leaf_fixture import merge,read_source,render,GUARD
F=0x80001000;R=0x80002000;A=0x80003000
W=0x60000000
class Fixture(unittest.TestCase):
    def test_merge(self):
        ws=(W,)*11+(0x4e800020,)
        call=0x48000001|((R-F)&0x03fffffc)
        old={F:(call,GUARD),R:(W,GUARD)}
        self.assertEqual(merge(old,F,R,F+4,ws),{F:(call,GUARD),R:ws})
        self.assertEqual(old[R],(W,GUARD))
        for bad in ({F:(call,W),R:(W,GUARD)},{F:(W,GUARD),R:(W,GUARD)},{F:(call,GUARD),R:(W,W)}):
            with self.assertRaises(ValueError):merge(bad,F,R,F+4,ws)
        with self.assertRaises(ValueError):merge(old,F,R,F+4,ws[:-1])
    def test_data_source(self):
        self.assertEqual(read_source((R,('const',A+2),2),((A,b'abcd'),),{},-864),(R,False,A+2,2,b'cd'))
        for ranges in ((),((A,b'abcd'),(A,b'abcd'))):
            with self.assertRaises(ValueError):read_source((R,('const',A+2),2),ranges,{},-864)
        with self.assertRaises(ValueError):read_source((R,('const',A+1),2),((A,b'abcd'),),{},-864)
    def test_stack_source(self):
        self.assertEqual(read_source((R,('stack',-860),1),(),{-860:('byte',255)},-864),(R,True,4,1,b'\xff'))
        with self.assertRaises(ValueError):read_source((R,('stack',-868),1),(),{},-864)
        with self.assertRaises(ValueError):read_source((R,('stack',-860),1),(),{-860:('part',('reg',3),4,0)},-864)
    def test_render(self):
        p=(None,None,None,(R,F+4,GUARD),(W,)*12,(R,),(R,True,4,1,b'\xff'),42)
        out=render(p)
        self.assertIn('stack_relative=true',out);self.assertIn('active,true,0x0000002au',out)
        self.assertIn('bytes{255u}',out)
if __name__=='__main__':unittest.main(verbosity=2)
