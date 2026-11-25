import unittest
from audit_handler_suffix_v728 import suffix,restore_suffix
R=0x80004000
NOP=0x60000000
BLR=0x4e800020
def lwz(r,b,d):return (32<<26)|(r<<21)|(b<<16)|(d&0xffff)
class HandlerSuffix(unittest.TestCase):
    def test_prefix(self):
        self.assertEqual(suffix(R,[NOP,0x41820008,0x48000101,BLR],R+4),
                         (3,0,0,[(R+8,1,1,R+0x108),(R+12,3,0,None)]))
    def test_loop_and_tail(self):
        self.assertEqual(suffix(R,[NOP,0x4082fffc,0x48000100],R),(3,1,0,[(R+8,2,0,R+0x108)]))
    def test_restore(self):
        words=[lwz(r,11,-4*(32-r)) for r in range(28,32)]+[BLR]
        self.assertEqual(restore_suffix(words),4)
        for i,w in ((0,lwz(28,3,-16)),(1,lwz(29,11,-8)),(4,NOP)):
            code=words.copy();code[i]=w;self.assertEqual(restore_suffix(code),0)
    def test_invalid(self):
        for root,words,start in ((R,[NOP],R),(R,[BLR],R+4),(R+1,[BLR],R+1)):
            with self.assertRaises(ValueError):suffix(root,words,start)
if __name__=='__main__':unittest.main()
