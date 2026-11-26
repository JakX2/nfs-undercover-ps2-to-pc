import unittest
from prepare_v1316_reply_helper import HELPER,BLR,leaf_shape,merge
NOP=0x60000000
class Tests(unittest.TestCase):
    def test_leaf(self):
        leaf_shape(HELPER,(NOP,BLR))
        for bad in ((NOP,), (0x48000001,BLR),(0x48000100,BLR),(0x4c000064,BLR)):
            with self.assertRaises(ValueError):leaf_shape(HELPER,bad)
    def test_expand(self):
        body=(NOP,NOP,BLR)
        self.assertEqual(merge({HELPER:(NOP,BLR)},body),{HELPER:body})
        for bad in ({},{HELPER:(BLR,BLR)},{HELPER:(NOP,BLR),HELPER+8:(NOP,BLR)}):
            with self.assertRaises(ValueError):merge(bad,body)
if __name__=='__main__':unittest.main()
