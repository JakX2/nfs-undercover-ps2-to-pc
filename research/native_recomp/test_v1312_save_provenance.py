import unittest
from save_provenance_v1312 import audit_save,BLR

def stw(r,d,base=3):return (36<<26)|(r<<21)|(base<<16)|d
def mf(r,s):return (31<<26)|(r<<21)|((s&31)<<16)|((s>>5)<<11)|(339<<1)
def li(r,n):return (14<<26)|(r<<21)|(n&0xffff)
def make():
    w=[stw(1,4),stw(2,8),(47<<26)|(13<<21)|(3<<16)|52]
    for ins,d in [(mf(0,8),132),((31<<26)|(19<<1),128),(mf(0,9),136),(mf(0,1),140),(mf(0,8),408),((31<<26)|(83<<1),412),(li(0,1),12)]:w.extend((ins,stw(0,d)))
    for i in range(1,8):w.extend((mf(0,912+i),stw(0,0x1a4+4*i)))
    return w+[li(3,0),BLR]
class Tests(unittest.TestCase):
    def test_valid(self):self.assertEqual(audit_save(make()),0xfe)
    def test_wrong_values(self):
        for i,w in [(0,stw(2,4)),(1,stw(2,8,4)),(3,mf(0,9)),(5,mf(0,8)),(15,li(0,0)),(17,mf(0,912))]:
            with self.subTest(i=i):
                a=make();a[i]=w
                with self.assertRaises(ValueError):audit_save(a)
    def test_control(self):
        for w in [0x48000004,0x44000002,0x4c000064,BLR]:
            with self.subTest(w=w):
                a=make();a[3]=w
                with self.assertRaises(ValueError):audit_save(a)
    def test_duplicate(self):
        a=make();a[1]=stw(2,4)
        with self.assertRaisesRegex(ValueError,'store geometry'):audit_save(a)
    def test_result(self):
        a=make();a[-2]=li(3,1)
        with self.assertRaisesRegex(ValueError,'provenance'):audit_save(a)
if __name__=='__main__':unittest.main()
