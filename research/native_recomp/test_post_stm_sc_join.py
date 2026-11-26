#!/usr/bin/env python3
import unittest
from prepare_post_stm_sc_join import prefix
from test_stm_final_return import ins,ST,MFLR,BLR
ROOT=0x80010000
TARGET=0x80020000
SITE=ROOT+16
def bl(pc,dst):return 0x48000001|((dst-pc)&0x03fffffc)
BODY=(ST,MFLR,ins(36,0,1,36),ins(36,31,1,28),bl(SITE,TARGET),BLR)
class Geometry(unittest.TestCase):
    def test_prefix(self):self.assertEqual(prefix(ROOT,BODY,SITE,TARGET),(5,3,1))
    def test_refusals(self):
        for body,site,target in ((BODY,SITE,TARGET+4),((BODY[0],BODY[1],ins(36,0,13,36),*BODY[3:]),SITE,TARGET),
            ((BODY[0],BODY[1],ins(32,0,13,36),*BODY[3:]),SITE,TARGET),((BODY[0],0x44000002,*BODY[2:]),SITE,TARGET),
            ((BODY[0],BODY[1],0x48000008,*BODY[3:]),SITE,TARGET), (BODY,SITE-4,TARGET)):
            with self.subTest(body=body,site=site,target=target),self.assertRaises(ValueError):prefix(ROOT,body,site,target)
if __name__=='__main__':unittest.main(verbosity=2)
