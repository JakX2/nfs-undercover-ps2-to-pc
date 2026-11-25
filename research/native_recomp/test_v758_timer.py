import unittest
from prepare_owner_timer_v758 import timer_kind
def spr(xo,number=22,reg=3):
    return (31<<26)|(reg<<21)|((number&31)<<16)|((number>>5)<<11)|(xo<<1)
class Timer(unittest.TestCase):
    def test_kinds(self):
        self.assertEqual(timer_kind([spr(467),0x4e800020]),1)
        self.assertEqual(timer_kind([spr(339),0x4e800020]),2)
        for w in (spr(467,23),spr(467,22,4),spr(467)|1,0x60000000):
            self.assertEqual(timer_kind([w,0x4e800020]),0)
        with self.assertRaises(ValueError):timer_kind([spr(467)])
if __name__=='__main__':unittest.main()
