#!/usr/bin/env python3
"""Synthetic SDA register and ACK accounting dataflow tests."""
import unittest
from prepare_ipc_deferred_ack_geometry import decrement_leaf,credit_sites,sda
B={2:0x80010000,13:0x80020000}
P=0x80030000
A=B[13]-4
def ins(op,reg,base,imm):return op<<26|reg<<21|base<<16|(imm&0xffff)
LW=ins(32,5,13,-4)
ST=ins(36,5,13,-4)
INC=ins(14,5,5,1)
DEC=ins(14,5,5,-1)
RET=0x4e800020
N=0x60000000
class Geometry(unittest.TestCase):
    def test_sda(self):
        self.assertEqual(sda(ST,36,B),A)
        self.assertIsNone(sda(ST,32,B))
        self.assertIsNone(sda(ins(36,5,3,-4),36,B))
    def test_profile(self):
        self.assertTrue(decrement_leaf((LW,DEC,ST,RET),A,B))
        for words in ((LW,INC,ST,RET),(LW,DEC,ins(36,6,13,-4),RET),
                      (LW,DEC,ins(36,5,13,-8),RET),(LW,DEC,ST,N),(LW,N,DEC,ST,RET)):
            with self.subTest(words=words),self.assertRaises(ValueError):decrement_leaf(words,A,B)
    def test_credit(self):
        self.assertEqual(credit_sites(P,(N,LW,INC,ST,N,N),A,P+20,B),1)
        for words in ((N,LW,DEC,ST,N,N),(N,LW,INC,N,N,N),(ST,LW,INC,ST,N,N),
                      (N,LW,N,ST,N,N),(N,ins(32,6,13,-4),INC,ST,N,N)):
            with self.subTest(words=words),self.assertRaises(ValueError):credit_sites(P,words,A,P+20,B)
if __name__=='__main__':unittest.main(verbosity=2)
