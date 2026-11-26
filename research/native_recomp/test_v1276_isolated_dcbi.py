import unittest
from apply_isolated_dcbi_v1276 import HID0,OLD_CTX,NEW_CTX,OLD_EMIT,NEW_EMIT,rewrite
class Isolated(unittest.TestCase):
    def test_exact(self):
        c=HID0+OLD_CTX;e=OLD_EMIT
        nc,ne,changed=rewrite(c,e)
        self.assertTrue(changed)
        self.assertEqual(nc,HID0+NEW_CTX)
        self.assertEqual(ne,NEW_EMIT)
        self.assertEqual(ne.count('xo == 470'),1)
        self.assertEqual(ne.count('ctx.guest_dcbi('),1)
        self.assertIn('guest_last_data_invalidate = line;',nc)
        self.assertEqual(rewrite(nc,ne),(nc,ne,False))
        for a,b in ((nc,e),(c,ne),(c+OLD_CTX,e),(c,e+e),(nc,ne+ne),
                    (OLD_CTX,e),(c+'uint32_t hid4',e),(c,e+'ctx.guest_dcbi(')):
            with self.assertRaises(ValueError):rewrite(a,b)
if __name__=='__main__':unittest.main()
