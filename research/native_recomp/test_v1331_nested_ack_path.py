import unittest
from derive_nested_ack_path_v1331 import derive
H=0x80004000;A=H+0x100;B=H+0x200;NOP=0x60000000;BLR=0x4e800020;CALL=0x4e800421;MT=0x7c600124
def bl(a,b):return 0x48000001|((b-a)&0x03fffffc)
def rows(root,words,guard=()):return [(root+i*4,w,root,i in guard) for i,w in enumerate(words)]
class Tests(unittest.TestCase):
    def fixture(self):
        r=rows(H,[NOP,bl(H+4,A),NOP,CALL],(3,))+rows(A,[bl(A,B),MT,BLR])+rows(B,[NOP,BLR])
        return r,[(H+4,A),(A,B)],[(A+4,MT)]
    def test_nested(self):
        r,e,m=self.fixture()
        self.assertEqual(derive(r,e,m,H,H,H+12,1,1),(H+4,A,((8,2,1),)))
    def test_unapproved_nested(self):
        r,e,m=self.fixture()
        for ee,mm in ((e[:1],m),(e,[])):
            with self.assertRaises(ValueError):derive(r,ee,mm,H,H,H+12,1,1)
    def test_second_handler_call(self):
        r,e,m=self.fixture()
        r=[(pc,bl(pc,A) if pc==H+8 else w,root,g) for pc,w,root,g in r]
        with self.assertRaises(ValueError):derive(r,e+[(H+8,A)],m,H,H,H+12,1,1)
    def test_wrong_frontier_and_count(self):
        r,e,m=self.fixture()
        for goal,visit in ((H+8,1),(H+12,2)):
            with self.assertRaises(ValueError):derive(r,e,m,H,H,goal,visit,1)
if __name__=='__main__':unittest.main()
