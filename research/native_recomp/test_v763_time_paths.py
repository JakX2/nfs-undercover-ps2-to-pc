import unittest
from audit_time_paths_v763 import counts,totals
H=0x80004000
NOP=0x60000000
BLR=0x4e800020
class Paths(unittest.TestCase):
    def test_conditional(self):
        self.assertEqual(counts(H,[0x4182000c,NOP,NOP,BLR]),{2,4})
    def test_loop(self):
        self.assertEqual(counts(H,[NOP,0x4082fffc,BLR],9),{3,5,7,9})
    def test_sum(self):
        self.assertEqual(totals([(H,[NOP]*4+[BLR]),(H,[NOP]*5+[BLR]),(H,[0x4182000c]+[NOP]*7+[BLR])]),{43,45})
    def test_refuse(self):
        for words in ([NOP],[0x48000100,BLR],[0x48000005,BLR]):
            with self.assertRaises(ValueError):counts(H,words)
if __name__=='__main__':unittest.main()
