import unittest
from prepare_owner_callback_time_v802 import extend
from prepare_owner_leaf_v714 import bl

class CallbackTime(unittest.TestCase):
    def test_extend(self):
        r=0x80004000;t=0x80006000
        words=[bl(r,r+0x100),0x60000000,bl(r+8,t),0x60000000,0x4e800020]
        self.assertEqual(extend(r,words,t),(r+8,words))
        with self.assertRaises(ValueError):extend(r,words,t+4)
        for i,w in ((1,0x4e800020),(3,0x4e800020)):
            bad=words[:];bad[i]=w
            with self.assertRaises(ValueError):extend(r,bad,t)
if __name__=='__main__':unittest.main()
