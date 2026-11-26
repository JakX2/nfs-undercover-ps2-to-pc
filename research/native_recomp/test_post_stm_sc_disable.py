#!/usr/bin/env python3
import unittest
from prepare_post_stm_sc_disable import leaf,BLR
def x(rs,ra,rb,xo):return (31<<26)|(rs<<21)|(ra<<16)|(rb<<11)|(xo<<1)
def rot(rs,ra,sh,mb,me):return (21<<26)|(rs<<21)|(ra<<16)|(sh<<11)|(mb<<6)|(me<<1)
BODY=(x(3,0,0,83),rot(3,4,0,17,15),x(4,0,0,146),rot(3,3,17,31,31),BLR)
class Leaf(unittest.TestCase):
    def test_valid(self):self.assertEqual(leaf(BODY),5)
    def test_refusals(self):
        for body in (BODY[:-1],(*BODY[:-1],0x44000002,BLR),(*BODY[:2],x(4,0,0,146),*BODY[2:]),
                     (x(31,0,0,83),*BODY[1:]),(BODY[0],rot(3,14,0,17,15),*BODY[2:]),
                     (BODY[0],0x90610000,*BODY[2:]),(*BODY[:-1],0x48000001,BLR)):
            with self.subTest(body=body),self.assertRaises(ValueError):leaf(body)
if __name__=='__main__':unittest.main(verbosity=2)
