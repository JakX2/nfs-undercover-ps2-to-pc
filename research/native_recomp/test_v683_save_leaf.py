import unittest
from unittest.mock import patch
from classify_save_leaf_v683 import classify_suffix,inspect_suffix,BLR
def stores(reg,base=11,op=36,disp=None):
    stride=4 if op==36 else 8
    if disp is None:disp=-(32-reg)*stride
    return tuple(op<<26|r<<21|base<<16|((disp+(r-reg)*stride)&0xffff) for r in range(reg,32))+(BLR,)
class Tests(unittest.TestCase):
    def test_all_suffixes(self):
        for reg in range(14,32):
            for op in (36,54):
                for base in (1,11):
                    self.assertEqual(classify_suffix(stores(reg,base,op)),{'kind':1 if op==36 else 2,'registers':32-reg,'base':base})
    def test_reject(self):
        good=stores(27)
        for bad in (good[:-1],good[:1]+(0x48000009,)+good[2:],good[:1]+(good[1]^0x10000,)+good[2:],good[:1]+(good[1]^4,)+good[2:],stores(13),stores(27,3),stores(27,11,37),stores(27,disp=0),stores(27,disp=-1024),good+(BLR,)):
            with self.assertRaises(ValueError):classify_suffix(bad)
    def test_authenticated_reads(self):
        good=stores(29);start=0x80004000
        def read(data,a,n):return (good[(a-start)//4],)
        with patch('classify_save_leaf_v683.words_at',side_effect=read),patch('classify_save_leaf_v683.read_words',side_effect=read):
            self.assertEqual(inspect_suffix(b'',b'',start)['registers'],3)
        with patch('classify_save_leaf_v683.words_at',side_effect=read),patch('classify_save_leaf_v683.read_words',return_value=[0]):
            with self.assertRaises(ValueError):inspect_suffix(b'',b'',start)
if __name__=='__main__':unittest.main()
