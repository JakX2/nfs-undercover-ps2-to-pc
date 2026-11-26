import unittest
from derive_allocator_census_v1345 import store_form,census
H=0x80004000;D=H+0x100;R=H+0x200;BLR=0x4e800020;NOP=0x60000000
def bl(a,b):return 0x48000001|((b-a)&0x03fffffc)
def d(op,rs,ra,imm):return op<<26|rs<<21|ra<<16|(imm&0xffff)
def x(xo,rs,ra,rb):return 31<<26|rs<<21|ra<<16|rb<<11|xo<<1
class Tests(unittest.TestCase):
    def test_forms(self):
        self.assertEqual(store_form(d(37,1,1,-32)),('scalar',4,1,True))
        self.assertEqual(store_form(d(47,28,1,16)),('multiple',16,1,False))
        self.assertEqual(store_form(x(151,4,5,6)),('indexed',4,5,False))
        self.assertIsNone(store_form(NOP))
        for w in (d(54,1,1,0),x(150,4,5,6),x(1014,0,5,6)):
            with self.assertRaises(ValueError):store_form(w)
    def test_census(self):
        ws=(d(37,1,1,-32),bl(H+4,D),d(36,4,5,0),bl(H+12,R),BLR)
        self.assertEqual(census(H,ws,((H+4,D),(H+12,R))),(5,1,{('scalar','stack',4,True):1,('scalar','other',4,False):1}))
        for edges in ((),((H+4,D),),((H+4,R),(H+12,R))):
            with self.assertRaises(ValueError):census(H,ws,edges)
    def test_control(self):
        for w in (0x44000002,0x4e800421,0x7c600124):
            with self.assertRaises(ValueError):census(H,(w,BLR),())
if __name__=='__main__':unittest.main()
