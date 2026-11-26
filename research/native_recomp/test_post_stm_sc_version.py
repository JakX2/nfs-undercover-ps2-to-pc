#!/usr/bin/env python3
import unittest
from prepare_post_stm_sc_version import thunk
B=0x80001000;R=0x80002000;SDA=0x80003000;PTR=0x80004000
def addi(rs,ra,n):return (14<<26)|(rs<<21)|(ra<<16)|(n&0xffff)
def mr(ra,rs):return (31<<26)|(rs<<21)|(ra<<16)|(rs<<11)|(444<<1)
def b(pc,dst):return 0x48000000|((dst-pc)&0x03fffffc)
class Version(unittest.TestCase):
    def test_thunk(self):
        words=(mr(4,3),addi(3,13,-16),b(B+8,R))
        self.assertEqual(thunk(B,words,R,{13:SDA},PTR),SDA-16)
        for body in ((mr(5,3),*words[1:]),(words[0],addi(3,12,-16),words[2]),
                     (*words[:-1],words[-1]|1),(*words[:-1],b(B+8,R+4)),
                     (words[0],0x90610000,words[2]),words[:-1]):
            with self.subTest(body=body),self.assertRaises(ValueError):thunk(B,body,R,{13:SDA},PTR)
if __name__=='__main__':unittest.main(verbosity=2)
