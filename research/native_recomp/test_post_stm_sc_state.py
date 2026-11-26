#!/usr/bin/env python3
import struct
import unittest
from prepare_post_stm_sc_state import initial,store_kind,overlap
class State(unittest.TestCase):
    def test_initial(self):
        d=bytearray(272)
        struct.pack_into('>I',d,0x1c,256)
        struct.pack_into('>I',d,0x64,0x80001000)
        struct.pack_into('>I',d,0xac,16)
        struct.pack_into('>II',d,0xd8,0x80002000,16)
        d[256:260]=b'\x12\x34\x56\x78'
        self.assertEqual(initial(bytes(d),0x80001000,4),(1,b'\x12\x34\x56\x78'))
        self.assertEqual(initial(bytes(d),0x80002000,4),(2,bytes(4)))
        for a,n in ((0x80001001,4),(0x80002010,1),(0x80001000,3),(0x80003000,4)):
            with self.subTest(a=a,n=n),self.assertRaises(ValueError):initial(bytes(d),a,n)
    def test_census(self):
        self.assertEqual(store_kind(36<<26),4)
        self.assertEqual(store_kind((47<<26)|(30<<21)),8)
        self.assertEqual(store_kind((31<<26)|(151<<1)),-1)
        self.assertEqual(store_kind(32<<26),0)
        self.assertTrue(overlap(10,4,13,4));self.assertFalse(overlap(10,4,14,4))
if __name__=='__main__':unittest.main(verbosity=2)
