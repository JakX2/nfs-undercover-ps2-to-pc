import unittest
from prepare_owner_cancel_v754 import queue_stores
from prepare_owner_leaf_v714 import bl
H=0x80004000
class Queue(unittest.TestCase):
    def test_direct_computed(self):
        stw=lambda r,b,d:(36<<26)|(r<<21)|(b<<16)|(d&0xffff)
        addi=lambda r,b,d:(14<<26)|(r<<21)|(b<<16)|(d&0xffff)
        words=[stw(0,13,-3496),addi(31,13,-3496),bl(H+8,H+0x100),stw(0,31,4),0x4e800020]
        self.assertEqual(queue_stores(H,words),((1,1),0))
        words[1]=addi(3,13,-3496);words[3]=stw(0,3,4)
        self.assertEqual(queue_stores(H,words),((1,0),1))
    def test_merge(self):
        # One branch clobbers the queue address; a merged unknown cannot
        # be counted as an authenticated store.
        words=[0x3bedf258,0x41820008,0x3be00000,0x901f0004,0x4e800020]
        self.assertEqual(queue_stores(H,words),((0,0),1))
if __name__=='__main__':unittest.main()
