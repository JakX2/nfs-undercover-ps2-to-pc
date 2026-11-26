#!/usr/bin/env python3
import unittest
from prepare_async_wrapper_return import corridor
S=0x80010000
R=0x80020000
N=0x60000000
RET=0x4e800020
def bl(pc,dst):return 0x48000001|((dst-pc)&0x03fffffc)
class Corridor(unittest.TestCase):
    def test_exact(self):
        body=(N,bl(S+4,R),0x80010004,0x7c0803a6,RET)
        self.assertEqual(corridor(S,body,S,S+4,R),(set(range(S,S+20,4)),{S+16}))
    def test_refusals(self):
        for body in ((N,bl(S+4,R+4),N,RET),(N,RET,N,RET),(N,bl(S+4,R),0x90010004,RET),
                     (N,bl(S+4,R),0x80610004,RET),(N,bl(S+4,R),0x4bfffffc,RET)):
            with self.subTest(body=body),self.assertRaises(ValueError):corridor(S,body,S,S+4,R)
if __name__=='__main__':unittest.main(verbosity=2)
