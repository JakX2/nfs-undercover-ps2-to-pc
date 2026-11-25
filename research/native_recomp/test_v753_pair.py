import unittest
from prepare_owner_pair_v753 import pair_shape,caller,H
def leaf(op,base,n,disp):
    return [(op<<26)|(r<<21)|(base<<16)|((disp+4*(r-(32-n)))&0xffff) for r in range(32-n,32)]+[0x4e800020]
class Pair(unittest.TestCase):
    def test_pair(self):
        for n in (6,11):
            self.assertEqual(pair_shape(leaf(36,11,n,-4*n),leaf(32,1,n,-4*n),n),(11,1,-4*n))
            self.assertEqual(len(caller(H+0x1000,H+0x2000,n)),n+4)
    def test_bad(self):
        s=leaf(36,11,6,-24);r=leaf(32,11,6,-24)
        for bad in (leaf(32,11,6,-28),leaf(32,11,5,-24),leaf(36,11,6,-24)):
            with self.assertRaises(ValueError):pair_shape(s,bad,6)
if __name__=='__main__':unittest.main()
