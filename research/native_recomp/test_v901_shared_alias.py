import unittest
from prepare_owner_transfer_callee_v901 import validate_roots
def save(first):
    return [(36<<26)|(r<<21)|(11<<16)|((-4*(32-r))&0xffff) for r in range(first,32)]+[0x4e800020]
class SharedAlias(unittest.TestCase):
    def test_shared(self):
        h=0x80004000
        roots={h:save(21),h+20:save(26),h+24:save(27)}
        self.assertEqual(validate_roots(roots,set(roots)),3)
        with self.assertRaises(ValueError):validate_roots(roots,{h})
        roots[h+20][0]^=1
        with self.assertRaises(ValueError):validate_roots(roots,set(roots))
    def test_nonoverlap(self):
        self.assertEqual(validate_roots({0x80004000:[0x4e800020],0x80004010:[0x4e800020]},set()),0)
if __name__=='__main__':unittest.main()
