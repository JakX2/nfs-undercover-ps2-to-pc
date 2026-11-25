import unittest
from audit_handler_path_v887 import rotate,step,unique_prefix
class HandlerAddress(unittest.TestCase):
    def test_rotate(self):
        self.assertEqual(rotate(0x80000001,1,0,31),3)
        self.assertEqual(rotate(0xffffffff,0,30,1),0xc0000003)
    def test_preserve(self):
        r=(None,)*32
        r=step(0x3c60cd00,r)
        r=step(0x3c800001,r)
        r=step(0x5484103a,r)
        self.assertEqual(r[3],0xcd000000)
        self.assertIsNone(r[5])
    def test_prefix(self):
        h=0x80004000
        words=[0x3c60cd00,0x3c800001,0x5484103a,0x3ca00000,0x7c842a14,0x80636434]
        rows={h+4*i:(w,0,0) for i,w in enumerate(words)}
        self.assertEqual(unique_prefix(rows,h)[0],'si')
if __name__=='__main__':unittest.main()
