import unittest
from prepare_v1383_stm_ioctl_entry import extend,scope,STM,STM_SIZE,IOCTL,DISABLE,BLR
class Tests(unittest.TestCase):
    def test_extent(self):
        body=tuple(range(STM_SIZE//4));disable=(BLR,);blocks={STM:body[:34]+(BLR,),DISABLE:disable}
        out=extend(blocks,body,1,disable)
        self.assertEqual(out[STM],body);self.assertEqual(out[IOCTL],(1,BLR))
        self.assertEqual(dict(scope({STM:96})),{STM:STM_SIZE,IOCTL:8})
        for b in ({STM:body[:33]+(BLR,),DISABLE:disable},{**blocks,IOCTL:(1,)},{**blocks,STM+140:(1,)}):
            with self.assertRaises(ValueError):extend(b,body,1,disable)
        with self.assertRaises(ValueError):scope({STM:96,IOCTL:8})
        with self.assertRaises(ValueError):scope({STM:96,STM+140:4})
if __name__=='__main__':unittest.main()
