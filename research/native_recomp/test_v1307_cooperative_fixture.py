import unittest
from prepare_v1307_cooperative_fixture import CLEAR,SAVE,BLR,leaf_shape,check_save,merge,call
NOP=0x60000000
def stw(r,off):return (36<<26)|(r<<21)|(3<<16)|off
def bl(pc,dst):return 0x48000001|((dst-pc)&0x03fffffc)
def save():
    words=[stw(0,o) for o in (4,8,12,128,132,136,140,408,412)]
    words.append((47<<26)|(13<<21)|(3<<16)|52)
    return tuple(words+[NOP]*(31-len(words))+[BLR])
class Tests(unittest.TestCase):
    def test_save_coverage(self):
        good=save();self.assertEqual(len(good),32);check_save(good)
        for bad in ((NOP,)+good[1:],good[:9]+(NOP,)+good[10:],good[:-1]+(NOP,),good[:-2]+(0x48000004,BLR),good[:-2]+(BLR,),good[:1]+(stw(0,8)^(1<<16),)+good[2:]):
            with self.assertRaises(ValueError):check_save(bad)
    def test_clear(self):
        leaf_shape(CLEAR,(NOP,BLR))
        for bad in ((NOP,), (0x48000001,BLR),(0x48000100,BLR),(0x4c000064,BLR)):
            with self.assertRaises(ValueError):leaf_shape(CLEAR,bad)
    def test_merge(self):
        roots={CLEAR:(NOP,NOP,BLR),SAVE:save()}
        old={CLEAR:(NOP,BLR),SAVE:save()}
        self.assertEqual(merge(old,roots),roots)
        for bad in ({CLEAR:(NOP,),SAVE:save()}, {CLEAR:(NOP,BLR),SAVE:(BLR,)},
                    {**old,CLEAR+8:(NOP,BLR)}):
            with self.assertRaises(ValueError):merge(bad,roots)
    def test_call(self):
        roots={SAVE:(bl(SAVE,CLEAR),BLR)}
        call(roots,SAVE,SAVE,CLEAR)
        with self.assertRaises(ValueError):call(roots,SAVE,SAVE,CLEAR+4)
        with self.assertRaises(ValueError):call(roots,SAVE,SAVE+8,CLEAR)
if __name__=='__main__':unittest.main()
