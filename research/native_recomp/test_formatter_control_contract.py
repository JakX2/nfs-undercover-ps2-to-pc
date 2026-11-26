import unittest
from prepare_formatter_control_contract import compare
from guarded_continuation import GUARD
R=0x80010000;A=0x80020000;B=0x80030000;C=0x80040000;L=0x80050000;N=0x60000000;W=0x80630000;BR=0x4e800420
class Test(unittest.TestCase):
    def setUp(self):
        rows=tuple((R+4*i,N) for i in range(74))
        fields=(R,L,R+296,W,48,C,4)
        access=tuple((R+4*i,1,-48+i,True,True) for i in range(14))+tuple((R+4*(30+i),4,A+4*i,False,False) for i in range(4))
        known=tuple((pc,at,b'abcd') for pc,n,at,stack,write in access if not stack)
        slots=((4,32),(-4,14),(-8,15),(-12,16))
        self.old=({R:(N,)*74+(W,GUARD)},fields,rows,access,slots,known)
        self.cells=((A,b'abcd'),(B,b'abcd'),(C,b'1234'))
        self.new=[{R:(N,)*74+(W,N,BR)+(GUARD,)*23+(N,GUARD)},(R,L,R+304,BR,48,0,0,R+400,N,383*4),rows+(fields[2:4],(R+300,N)),access+((R+296,4,C,False,False),),slots,known+((R+296,C,b'1234'),)]
    def test_exact(self):self.assertEqual(compare(self.old,self.new,self.cells),self.new)
    def test_candidate(self):
        with self.assertRaisesRegex(ValueError,'candidate'):compare(self.old,self.new,self.cells[:2]+((C,b'xxxx'),))
    def test_stop(self):
        self.new[1]=self.new[1][:7]+(R,N,383*4)
        with self.assertRaisesRegex(ValueError,'stop'):compare(self.old,self.new,self.cells)
    def test_target(self):
        self.new[1]=self.new[1][:8]+(W,383*4)
        with self.assertRaisesRegex(ValueError,'target'):compare(self.old,self.new,self.cells)
    def test_slots(self):
        self.new[4]=self.new[4][:-1]
        with self.assertRaisesRegex(ValueError,'slots'):compare(self.old,self.new,self.cells)
if __name__=='__main__':unittest.main(verbosity=2)
