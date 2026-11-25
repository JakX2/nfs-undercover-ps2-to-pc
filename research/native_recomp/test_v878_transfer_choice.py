import unittest
from prepare_owner_transfer_choice_v878 import choice
H=0x80004000;NOP=0x60000000;CALL=0x48000101
class TransferChoice(unittest.TestCase):
    def test_forward(self):
        words=[CALL,CALL,0x41820008,CALL,CALL]
        rows,stops=choice(H,words,H+8)
        self.assertEqual(len(rows),3);self.assertEqual([x[2] for x in stops],[3,4])
    def test_refuse(self):
        for words in ([CALL,CALL,0x48000000],[CALL,CALL,0x4e800020],[CALL,CALL,0x4e800421],[CALL,CALL,0x48000100]):
            with self.assertRaises(ValueError):choice(H,words,H+8)
if __name__=='__main__':unittest.main()
