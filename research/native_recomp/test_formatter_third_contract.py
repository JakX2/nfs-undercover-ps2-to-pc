import unittest
from prepare_formatter_third_contract import compare
from guarded_continuation import GUARD
R=0x80010000;A=0x80020000;B=0x80030000;C=0x80040000;L=0x80050000;N=0x60000000;W=0x80630000
class Test(unittest.TestCase):
    def setUp(self):
        rows=tuple((R+4*i,N) for i in range(44))
        fields=(R,L,R+176,W,48,B,4)
        access=tuple((R+4*i,1,-48+i,True,True) for i in range(12))+((R+48,4,C,False,False),(R+140,4,A,False,False))
        slots=((4,32),);known=((R+48,C,b'abcd'),(R+140,A,b'1234'))
        self.old=({R:(N,)*44+(W,GUARD)},fields,rows,access,slots,known)
        self.cells=((A,b'1234'),(B,b'5678'))
        more=((R+176,4,B,False,False),(R+180,4,-8,True,True),(R+184,4,-8,True,False),(R+188,4,C+4,False,False))
        self.new=[{R:(N,)*44+(W,)+(N,)*30+(GUARD,)},(R,L,R+296,W,48,C+8,4),rows+(fields[2:4],)+tuple((R+4*i,N) for i in range(45,74)),access+more,slots,known+((R+176,B,b'5678'),(R+188,C+4,b'zzzz'))]
    def test_exact(self):self.assertEqual(compare(self.old,self.new,self.cells),self.new)
    def test_prefix(self):
        self.new[2]=self.new[2][1:]+((R,N),)
        with self.assertRaisesRegex(ValueError,'prefix'):compare(self.old,self.new,self.cells)
    def test_count(self):
        x=list(self.new[3]);x[-1]=(*x[-1][:4],True);self.new[3]=tuple(x)
        with self.assertRaisesRegex(ValueError,'counts'):compare(self.old,self.new,self.cells)
    def test_candidate(self):
        with self.assertRaisesRegex(ValueError,'candidate'):compare(self.old,self.new,(self.cells[0],(B,b'xxxx')))
    def test_slots(self):
        self.new[4]=()
        with self.assertRaisesRegex(ValueError,'slots'):compare(self.old,self.new,self.cells)
    def test_word(self):
        self.new[0][R]=(W,)+self.new[0][R][1:]
        with self.assertRaisesRegex(ValueError,'old words'):compare(self.old,self.new,self.cells)
if __name__=='__main__':unittest.main(verbosity=2)
