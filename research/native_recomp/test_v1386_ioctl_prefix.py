import unittest
from prepare_v1386_ioctl_prefix import merge,check_spans,IOCTL,SIZE,SAVE,RESTORE,BLR
class TestPrefix(unittest.TestCase):
    def test_merge(self):
        word=0x60000000
        roots={IOCTL:(word,)*(SIZE//4-1)+(BLR,),SAVE:(word,BLR),RESTORE:(word,BLR)}
        old={IOCTL:(word,BLR),0x80004000:(BLR,)}
        out=merge(old,roots)
        self.assertEqual(len(out),4)
        self.assertEqual(old[IOCTL],(word,BLR))
        self.assertEqual(out[IOCTL],roots[IOCTL])
        for bad in ({**old,IOCTL:(BLR,BLR)},{**old,SAVE:(BLR,)},{**old,IOCTL+8:(BLR,)}):
            with self.assertRaises(ValueError):merge(bad,roots)
        with self.assertRaises(ValueError):check_spans({0x80004000:8,0x80004004:4})
        with self.assertRaises(ValueError):check_spans({0x80004001:4})
if __name__=='__main__':unittest.main()
