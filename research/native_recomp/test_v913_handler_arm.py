import unittest
from audit_handler_arm_v913 import ea,location
class Arm(unittest.TestCase):
    def test_ea(self):
        r=[None]*32;r[3]=0x80090000;r[4]=8
        self.assertEqual(ea(0x80830004,r),0x80090004)
        self.assertEqual(ea((31<<26)|(5<<21)|(3<<16)|(4<<11)|(23<<1),r),0x80090008)
        self.assertEqual(location(0xcd006438,[]),'si_status')
        self.assertEqual(location(0x80090004,[(0x80090000,0x80090008)]),'data')
if __name__=='__main__':unittest.main()
