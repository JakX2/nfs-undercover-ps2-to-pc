import unittest
from prepare_v1321_combined_resume import CLEAR,HELPER,expand_scope,merge
NOP=0x60000000
BLR=0x4e800020
H=(NOP,)*30+(BLR,)
C=(NOP,)*8+(BLR,)
class Tests(unittest.TestCase):
    def test_scope(self):
        sizes={CLEAR:0x24,HELPER:0x7c}
        self.assertEqual(dict(expand_scope([(CLEAR,8),(HELPER,0x7c)],sizes)),sizes)
        for prior in ([(CLEAR,0x24),(HELPER,0x7c)],[(CLEAR,8),(HELPER,8)],[(CLEAR,8),(HELPER,0x7c),(CLEAR+8,4)]):
            with self.assertRaises(ValueError):expand_scope(prior,sizes)
    def test_merge(self):
        old={CLEAR:(NOP,BLR),HELPER:H}
        self.assertEqual(merge(old,{CLEAR:C},H),{CLEAR:C,HELPER:H})
        self.assertEqual(old[CLEAR],(NOP,BLR))
        for prior in ({CLEAR:(NOP,BLR),HELPER:(NOP,BLR)},{CLEAR:(NOP,BLR)},
                      {**old,CLEAR+8:(BLR,)}):
            with self.assertRaises(ValueError):merge(prior,{CLEAR:C},H)
        with self.assertRaises(ValueError):merge(old,{CLEAR:C,HELPER:H},H)
if __name__=='__main__':unittest.main()
