import unittest
from audit_osinit_suffix_v929 import category,first_region
R=0x80004000
BL=0x48001001;NOP=0x60000000;BLR=0x4e800020
class Census(unittest.TestCase):
    def test_straight(self):
        rows,back,stores,stop=first_region(R,[NOP,0x80640000,0x90640004,BL,BLR],R)
        self.assertEqual((len(rows),back,stores,len(stop)),(4,0,1,1))
        self.assertEqual([category(w) for w in rows.values()],['integer','load','store','direct'])
    def test_branch(self):
        rows,back,stores,stop=first_region(R,[0x41820008,BL,BL],R)
        self.assertEqual((len(rows),back,stores,len(stop)),(3,0,0,2))
        self.assertEqual({s[2] for s in stop},{1,2})
    def test_bad(self):
        for ws in ([NOP],[0x48001000],[0x4d820020,NOP,BLR]):
            with self.assertRaises(ValueError):first_region(R,ws,R)
if __name__=='__main__':unittest.main()
