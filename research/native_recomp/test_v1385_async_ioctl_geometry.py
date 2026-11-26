import unittest
from prepare_v1385_async_ioctl_geometry import leaf_shape,wrapper_shape,SIZE,BLR
def leaf(op,first=26,base=11,disp=-24):
    return tuple((op<<26)|(r<<21)|(base<<16)|((disp+4*(r-first))&0xffff) for r in range(first,32))+(BLR,)
class Tests(unittest.TestCase):
    def test_leaves(self):
        self.assertEqual(leaf_shape(leaf(36)),(6,11,-24))
        self.assertEqual(leaf_shape(leaf(32),True),(6,11,-24))
        for words,restore in ((leaf(32),False),(leaf(36),True),(leaf(36,base=3),False),
                              (leaf(32,disp=4),True),(leaf(36)[:-1],False)):
            with self.assertRaises(ValueError):leaf_shape(words,restore)
    def test_wrapper(self):
        r=0x80004000;t=r+0x1000;n=SIZE//4
        w=[0x60000000]*n;w[0]=0x48000001|((t-r)&0x03fffffc);w[-1]=BLR
        seen,returns,stores,sda=wrapper_shape(w,r,((r,t),))
        self.assertEqual((len(seen),len(returns),len(stores),len(sda)),(n,1,0,0))
        for bad,edges in ((w[:-1],((r,t),)),(w,((r,t+4),)),([BLR]+w[1:],((r,t),)),(w[:-1]+[0x60000000],((r,t),))):
            with self.assertRaises(ValueError):wrapper_shape(bad,r,edges)
if __name__=='__main__':unittest.main()
