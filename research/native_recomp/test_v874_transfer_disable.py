import unittest
from prepare_owner_transfer_disable_v874 import continuation
H=0x80004000;D=H+0x100
NOP=0x60000000;CALL=0x48000101
class TransferDisable(unittest.TestCase):
    def test_linear(self):
        w=0x48000001|((D-(H+8))&0x03fffffc)
        self.assertEqual(continuation(H,[NOP,NOP,w,NOP],H+4,D),(H+8,[NOP,w],NOP))
    def test_refuse(self):
        w=0x48000001|((D-(H+8))&0x03fffffc)
        for code,start,target in (([NOP,NOP,w,NOP],H+5,D),([NOP,NOP,w,NOP],H+4,D+4),
             ([NOP,0x48000004,w,NOP],H+4,D),([NOP,NOP,w,0x4e800020],H+4,D),
             ([NOP,NOP,NOP,NOP],H+4,D)):
            with self.assertRaises(ValueError):continuation(H,code,start,target)
if __name__=='__main__':unittest.main()
