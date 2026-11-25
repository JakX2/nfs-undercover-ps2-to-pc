import unittest
from audit_handler_third_v740 import edge,summarize
from prepare_owner_leaf_v714 import bl
H=0x80004000
class Third(unittest.TestCase):
    def test_edge(self):
        code=[0x90010004,bl(H+4,H+0x100),0x4e800421,bl(H+12,H+0x200),0x4e800020]
        self.assertEqual(edge(H,code,3),(H+12,H+0x200,code[3]))
        with self.assertRaises(ValueError):edge(H,code,2)
        with self.assertRaises(ValueError):edge(H,code,4)
    def test_shape(self):
        row,edges=summarize(H,[0x80010004,0x90010004,0x4082fffc,bl(H+12,H+0x100),0x4e800421,0x4d820020,0x4e800020])
        self.assertEqual((row['loads'],row['stores'],row['backward'],row['direct'],row['indirect'],row['returns']),(1,1,1,1,1,2))
        self.assertEqual(edges,[(1,H+0x100),(2,None)])
if __name__=='__main__':unittest.main()
