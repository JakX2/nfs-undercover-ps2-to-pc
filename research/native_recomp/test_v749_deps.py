import unittest
from audit_handler_deps_v749 import graph
from prepare_owner_leaf_v714 import bl
H=0x80004000
class Graph(unittest.TestCase):
    def test_edges(self):
        self.assertEqual(graph(H,[bl(H,H+0x100),0x4e800421,0x40820008,0x4bfffff4,0x4e800020]),[(1,H+0x100),(2,None)])
        self.assertEqual(graph(H,[0x48000100]),[(3,H+0x100)])
    def test_invalid(self):
        for a,w in ((H+1,[0x4e800020]),(H,[]),(H,[0x60000000]*1025)):
            with self.assertRaises(ValueError):graph(a,w)
if __name__=='__main__':unittest.main()
