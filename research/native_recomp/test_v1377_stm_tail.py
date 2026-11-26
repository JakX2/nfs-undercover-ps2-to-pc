import unittest
from prepare_v1377_stm_tail import scan
A=0x80004000
B=0x80005000
NOP=0x60000000
BLR=0x4e800020
def bl(pc,dst):return 0x48000001|((dst-pc)&0x03fffffc)
def bc(pc,dst):return 0x41820000|((dst-pc)&0xfffc)
class Tests(unittest.TestCase):
    def test_tail(self):
        words=(NOP,bc(A+4,A+16),bl(A+8,B),0x906d0000,BLR)
        seen,calls,returns,stores,sda=scan(A,words,A,{A+8:B})
        self.assertEqual((len(seen),len(calls),len(returns),len(stores),len(sda)),(5,1,1,1,1))
    def test_fail_closed(self):
        for words,start,allowed in (
            ((NOP,),A,{}),
            ((BLR,),A+4,{}),
            ((bl(A,B),BLR),A,{}),
            ((bl(A,B),BLR),A,{A:B+4}),
            ((BLR,bl(A+4,B)),A,{A+4:B}),
            ((0x44000002,BLR),A,{}),
            ((0x4e800420,BLR),A,{}),
            ((bc(A,A+8),BLR),A,{}),
            ((0x48000000,),A,{})):
            with self.subTest(words=words,start=start):
                with self.assertRaises(ValueError):scan(A,words,start,allowed)
if __name__=='__main__':unittest.main()
