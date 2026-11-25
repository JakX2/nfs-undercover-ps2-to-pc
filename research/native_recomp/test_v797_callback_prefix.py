import unittest
from prepare_owner_callback_prefix_v797 import prologue_word, prefix_geometry
from prepare_owner_leaf_v714 import bl

class CallbackPrefix(unittest.TestCase):
    def test_geometry(self):
        root=0x80006000
        prefix=[0x9421ffc0,0x7c0802a6,0x90010044,0x39610040]
        site=root+4*len(prefix)
        w=bl(site,0x80008000)
        code=prefix+[w,0x7c7f1b78,0x4e800020]
        self.assertEqual(prefix_geometry(root,code),(site,0x80008000,code))
        for i,bad in ((0,0x60000000),(1,0x7c0902a6),(2,0x90030044),(3,0x48000004),(4,0x4e800421),(5,0x4e800020)):
            broken=code[:];broken[i]=bad
            with self.assertRaises(ValueError):prefix_geometry(root,broken)
    def test_word(self):
        self.assertTrue(prologue_word(0x7c7f1b78))
        self.assertFalse(prologue_word(0x7c7f1b79))
        self.assertFalse(prologue_word(0x7c000124))
        self.assertFalse(prologue_word(0x94210020))

if __name__=='__main__':unittest.main()
