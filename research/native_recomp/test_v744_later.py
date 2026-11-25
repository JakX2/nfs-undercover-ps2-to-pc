import unittest
from audit_handler_later_v744 import walk
from prepare_owner_leaf_v714 import bl
H=0x80004000
class Later(unittest.TestCase):
    def test_walk(self):
        code=[0x90010004,bl(H+4,H+0x100),0x41820008,bl(H+12,H+0x200),0x4e800421,0x4e800020]
        self.assertEqual(walk(H,code,H+8),(4,1,0,[(2,H+0x200),(3,None)]))
    def test_missing_return(self):
        with self.assertRaises(ValueError):walk(H,[0x90010004,bl(H+4,H+0x100)],H+4)
    def test_external(self):
        self.assertEqual(walk(H,[0x90010004,0x48000100],H+4),(1,0,1,[]))
if __name__=='__main__':unittest.main()
