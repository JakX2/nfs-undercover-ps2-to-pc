import unittest
from make_v624_ipc_geometry import constants,derive_handler,render,ROUTE,ROOT,EDGES
def imm(op,rd,ra,n):return op<<26|rd<<21|ra<<16|(n&0xffff)
def mr(dst,src):return 31<<26|src<<21|dst<<16|src<<11|444<<1
class Tests(unittest.TestCase):
    def test_const(self):
        p=0x80519094
        # Signed low half of an HA16/LO16 relocation.
        words=[imm(15,3,0,0x8052),imm(14,4,3,0x9094),imm(14,3,0,27)]
        self.assertEqual(derive_handler(words,{p:64}),(p,64))
        self.assertEqual(derive_handler([imm(15,5,0,0x8051),imm(24,5,5,0x9094),mr(4,5),imm(14,3,0,27)],{p:64}),(p,64))
        for bad in (words[:-1],words+[imm(14,4,0,0)],words+[0x48000001],words+[imm(14,3,0,26)],
                    [imm(14,4,4,0x9094),imm(14,3,0,27)]):
            with self.assertRaises(ValueError):derive_handler(bad,{p:64})
        for symbols in ({},{p:0},{p:0x1004},{p:ROOT-p+4}):
            with self.assertRaises(ValueError):derive_handler(words,symbols)
        self.assertEqual(constants([imm(15,4,0,0xffff),imm(14,4,4,-1)])[4],0xfffeffff)
    def test_route(self):
        self.assertEqual(len(ROUTE),17);self.assertEqual(len(set(ROUTE)),17)
        self.assertTrue(set(EDGES).issubset(ROUTE))
        self.assertEqual(ROUTE[12:15],((0x805269d8,0x805265ac),(0x80526a08,0x805266e0),(0x80526a18,0x805265d4)))
        rows=[(t,s+4,1,2) for s,t in ROUTE]
        h=render(rows,0x80519094,3,4)
        self.assertIn('std::array<VectorEdge,17>{',h);self.assertEqual(h.count('VectorEdge{'),17)
        with self.assertRaises(ValueError):render(rows[:-1],0,0,0)
if __name__=='__main__':unittest.main()
