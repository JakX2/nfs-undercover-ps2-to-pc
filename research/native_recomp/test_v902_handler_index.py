import unittest
from audit_handler_index_v902 import address
class IndexedLoad(unittest.TestCase):
    def test_index(self):
        r=[0]*32;r[3]=0x80090000;r[4]=12
        w=(31<<26)|(5<<21)|(3<<16)|(4<<11)|(23<<1)
        self.assertEqual(address(w,r),0x8009000c)
        r[4]=None;self.assertIsNone(address(w,r))
        with self.assertRaises(ValueError):address(0x60000000,r)
if __name__=='__main__':unittest.main()
