import unittest
from audit_formatter_partial_stack_read import known_mask,consumer
def rlwinm(rs,ra,sh,mb,me):return (21<<26)|(rs<<21)|(ra<<16)|(sh<<11)|(mb<<6)|(me<<1)
class Test(unittest.TestCase):
    def test_mask(self):
        self.assertEqual(known_mask({0:('byte',0),1:('byte',0),2:('part',('reg',3),4,2)},0,4),0xffff0000)
    def test_rotation(self):
        self.assertEqual(consumer(rlwinm(3,3,16,16,31),3,0xffff0000),('rotate_mask',1,1,16))
        self.assertEqual(consumer(rlwinm(3,4,0,16,31),3,0xffff0000),('rotate_mask',0,0,16))
    def test_and(self):
        self.assertEqual(consumer((29<<26)|(3<<21)|(3<<16)|0xff00,3,0xffff0000),('and_immediate',1,1,8))
    def test_extend(self):
        self.assertEqual(consumer((31<<26)|(3<<21)|(4<<16)|(922<<1),3,0xffff),('sign_extend',1,0,16))
    def test_other(self):
        self.assertEqual(consumer(0x60000000,3,0xffffffff),('other',0,0,32))
if __name__=='__main__':unittest.main(verbosity=2)
