import unittest
from collect_third_alarm_suffix_v1044 import collect_after_alarm as collect
H=0x80004000;NOP=0x60000000;BLR=0x4e800020;BCTRL=0x4e800421
def bl(pc,dst):return 0x48000001|((dst-pc)&0x3fffffc)
class Suffix(unittest.TestCase):
    def test_original_and_guard_terminal(self):
        # Five earlier linked calls set the sixth original call ordinal.
        code=[bl(H+i*4,H+0x1000) for i in range(5)]+[NOP,0x41820008,BCTRL,0x44000002]
        translated=code.copy();translated[-1]=BLR
        rows=collect(H,code,translated,{H+32},H+20)
        self.assertEqual(rows[H+28],(BCTRL,6,2))
        self.assertEqual(rows[H+32],(BLR,0,0))
        self.assertEqual(len(rows),4)
    def test_guard_before_otherwise_invalid_branch(self):
        code=[NOP,0x48000100]
        self.assertEqual(collect(H,code,[NOP,BLR],{H+4},H),{H:(NOP,0,0),H+4:(BLR,0,0)})
        with self.assertRaisesRegex(ValueError,'extent'):collect(H,code,code,set(),H)
    def test_refusals(self):
        for code,out,guards in (([NOP,BLR],[NOP,NOP],{H+4}),([NOP,BLR],[BLR,BLR],set()),
                                 ([0x44000002],[0x44000002],set()),([0x48000000],[0x48000000],set())):
            with self.assertRaises(ValueError):collect(H,code,out,guards,H)
if __name__=='__main__':unittest.main()
