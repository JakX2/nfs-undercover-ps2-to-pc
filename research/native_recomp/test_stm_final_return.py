#!/usr/bin/env python3
"""Synthetic ABI provenance tests; no original executable needed."""
import unittest
from prepare_stm_final_return import prologue,tail,BLR
def ins(op,rs,ra,n):return (op<<26)|(rs<<21)|(ra<<16)|(n&0xffff)
def spr(op,rs,n):return (31<<26)|(rs<<21)|((n&31)<<16)|((n>>5)<<11)|(op<<1)
ST=ins(37,1,1,-32)
MFLR=spr(339,0,8)
MTLR=spr(467,0,8)
SAVE=(ST,MFLR,ins(36,0,1,36),ins(47,30,1,24))
REST=(ins(32,0,1,36),ins(46,30,1,24),MTLR,ins(14,1,1,32),BLR)
class ReturnGeometry(unittest.TestCase):
    def test_valid(self):
        frame,slots=prologue(SAVE)
        self.assertEqual(frame,32)
        self.assertEqual(tail(REST,frame,slots),(3,2))
    def test_prologue_order(self):
        self.assertEqual(prologue((MFLR,ST,*SAVE[2:])),prologue(SAVE))
    def test_individual_loads(self):
        f,s=prologue(SAVE)
        self.assertEqual(tail((REST[0],ins(32,30,1,24),ins(32,31,1,28),*REST[2:]),f,s),(3,2))
    def test_volatile_return_arithmetic(self):
        f,s=prologue(SAVE)
        self.assertEqual(tail((REST[0],REST[1],ins(14,3,30,0),REST[2],*REST[3:]),f,s),(3,2))
        with self.assertRaises(ValueError):tail((REST[0],REST[1],ins(14,0,0,7),REST[2],*REST[3:]),f,s)
        with self.assertRaises(ValueError):tail((REST[0],REST[1],ins(14,30,0,7),REST[2],*REST[3:]),f,s)
    def test_bad_prologue(self):
        for bad in ((MFLR,), (ST,MFLR,ins(36,0,1,40)),
                    (ST,MFLR,ins(36,0,1,36),ins(36,0,1,28)),
                    (ST,MFLR,ins(36,0,1,36),ins(36,30,1,36)),
                    (ins(37,1,1,-12),MFLR,*SAVE[2:])):
            with self.subTest(bad=bad),self.assertRaises(ValueError):prologue(bad)
    def test_bad_tail(self):
        f,s=prologue(SAVE)
        for bad in ((REST[0],*REST[2:]), (REST[0],REST[1],ins(36,0,1,16),*REST[2:]),
                    (ins(32,0,1,32),*REST[1:]), (REST[0],REST[1],spr(467,4,8),*REST[3:]),
                    (*REST[:3],ins(14,1,1,16),BLR),(*REST[:-1],0x48000001,BLR),
                    (BLR,*REST),(*REST[:-1],ins(32,14,1,36),BLR)):
            with self.subTest(bad=bad),self.assertRaises(ValueError):tail(bad,f,s)
if __name__=='__main__':unittest.main(verbosity=2)
