#!/usr/bin/env python3
import unittest
from prepare_async_submit_return import corridor
S=0x80010000
R=0x80020000
N=0x60000000
RET=0x4e800020
def bl(pc,dst):return 0x48000001|((dst-pc)&0x03fffffc)
class Corridor(unittest.TestCase):
    def test_exact(self):
        body=(N,bl(S+4,R),N,RET)
        self.assertEqual(corridor(S,body,S,S+4,R),({S,S+4,S+8,S+12},{S+12}))
    def test_forbidden(self):
        for body in ((N,bl(S+4,R+4),N,RET),(N,bl(S+4,R),bl(S+8,R),RET),(N,RET,N,RET)):
            with self.subTest(body=body),self.assertRaises(ValueError):corridor(S,body,S,S+4,R)
if __name__=='__main__':unittest.main(verbosity=2)
