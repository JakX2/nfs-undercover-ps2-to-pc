#!/usr/bin/env python3
import unittest
from prepare_stm_outer_restore import select
R=0x80010000
N=0x60000000
MT=0x7c000124
class Geometry(unittest.TestCase):
    def test_exact(self):self.assertEqual(select(R,(N,MT,N),[R,R+4,R+8]),(R+4,R+8))
    def test_refusals(self):
        for body,labels in (((N,N,N),[R,R+4,R+8]),((MT,MT,N),[R,R+4,R+8]),((N,MT,N),[R,R+4])):
            with self.subTest(body=body),self.assertRaises(ValueError):select(R,body,labels)
if __name__=='__main__':unittest.main(verbosity=2)
