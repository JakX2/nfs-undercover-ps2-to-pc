import unittest
from prepare_owner_scheduler_v722 import shapes,E,S,BLR
from prepare_owner_leaf_v714 import bl
D=E-0x100
R=E-0x200
G=S+0x100
NOP=0x60000000
def mem(op,disp):return (op<<26)|(3<<21)|(13<<16)|(disp&0xffff)
def tail(a,b):return bl(a,b)&~1
class SchedulerGeometry(unittest.TestCase):
    def samples(self):
        e=[bl(E,D),mem(32,-4),mem(36,-4),bl(E+12,R)]+[NOP]*10+[BLR]
        s=[mem(32,-8),NOP,0x4182000c,NOP,tail(S+16,G),BLR]
        return e,s
    def test_shape(self):
        e,s=self.samples();self.assertEqual(shapes(e,s,D,R),(-4,-8,[(E,D),(E+12,R)],(S+16,G)))
    def test_invalid(self):
        for k,i,w in ((0,2,mem(36,-8)),(0,3,bl(E+12,D)),(1,0,mem(32,-4)),(1,4,bl(S+16,G)),(1,3,0x4e800421)):
            e,s=self.samples();(e,s)[k][i]=w
            with self.assertRaises(ValueError):shapes(e,s,D,R)
if __name__=='__main__':unittest.main()
