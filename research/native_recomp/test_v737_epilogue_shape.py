import unittest
from prepare_owner_epilogue_v737 import dispatcher_shape,E,S,L
from prepare_owner_leaf_v714 import bl
J=0x80526000
def mr(src,dst=3):return (31<<26)|(src<<21)|(dst<<16)|(src<<11)|(444<<1)
class EpilogueShape(unittest.TestCase):
    def test_shape(self):
        self.assertEqual(dispatcher_shape(J,[bl(J,E),bl(J+4,S),mr(29),bl(J+12,L)]),29)
    def test_refusal(self):
        base=[bl(J,E),bl(J+4,S),mr(29),bl(J+12,L)]
        for i,w in ((0,bl(J,S)),(1,bl(J+4,E)),(2,mr(3)),(2,mr(29,4)),(2,mr(29)|1),(3,bl(J+12,E))):
            words=base.copy();words[i]=w
            with self.assertRaises(ValueError):dispatcher_shape(J,words)
if __name__=='__main__':unittest.main()
