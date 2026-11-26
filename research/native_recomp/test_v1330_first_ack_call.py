import unittest
from derive_first_ack_call_v1330 import first_calls,classify
H=0x80004000;A=H+0x100;B=H+0x200;NOP=0x60000000
def bl(pc,dst):return 0x48000001|((dst-pc)&0x03fffffc)
def bc(pc,dst):return 0x41820000|((dst-pc)&0xfffc)
def graph(words,guards=()):return [(H+i*4,w,H,i in guards) for i,w in enumerate(words)]
class Tests(unittest.TestCase):
    def test_first_direct_call(self):
        rows=graph([NOP,bc(H+4,H+16),NOP,bl(H+12,A),bl(H+16,B)])
        edges=[(H+12,A),(H+16,B)]
        self.assertEqual(first_calls(rows,edges,H,H),((2,2),(3,1)))
        self.assertEqual(classify(rows,edges,H,H,3),(2,))
        self.assertEqual(classify(rows,edges,H,H,4),(1,))
    def test_guard_and_wrong_edge(self):
        rows=graph([NOP,bl(H+4,A)],(1,))
        self.assertEqual(first_calls(rows,[],H,H),())
        rows=graph([NOP,bl(H+4,A)])
        for edges in ([],[(H+4,B)],[(H+4,A),(H+4,A)]):
            with self.assertRaises(ValueError):first_calls(rows,edges,H,H)
    def test_already_counted(self):
        rows=graph([bl(H,A),bl(H+4,B)])
        self.assertEqual(first_calls(rows,[(H,A),(H+4,B)],H,H),((0,1),))
    def test_loop(self):
        rows=graph([NOP,bc(H+4,H+4),bl(H+8,A)])
        self.assertEqual(first_calls(rows,[(H+8,A)],H,H,4),((2,1),(3,1),(4,1)))
if __name__=='__main__':unittest.main()
