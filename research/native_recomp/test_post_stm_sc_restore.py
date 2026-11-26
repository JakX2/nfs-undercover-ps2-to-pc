#!/usr/bin/env python3
import unittest
from prepare_post_stm_sc_restore import leaf
B=0x80001000
def x(rs,ra,rb,xo):return (31<<26)|(rs<<21)|(ra<<16)|(rb<<11)|(xo<<1)
def words(ws):return {B+4*i:(B,w) for i,w in enumerate(ws)}
BODY=(x(0,0,0,83),0x60000000,x(0,0,0,146),0x4c00012c,0x4e800020)
class Restore(unittest.TestCase):
    def test_leaf(self):
        self.assertEqual(leaf(words(BODY),B,B+8,B+12),5)
        for body in (BODY[:-1],(*BODY[:-1],0x44000002,0x4e800020),(BODY[0],0x90610000,*BODY[2:]),
                     (BODY[0],0x48000000,*BODY[2:]),(BODY[0],x(0,0,0,146),*BODY[2:])):
            with self.subTest(body=body),self.assertRaises(ValueError):leaf(words(body),B,B+8,B+12)
if __name__=='__main__':unittest.main(verbosity=2)
