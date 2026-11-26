import unittest
from prepare_formatter_post_ctr_contract import compare
from guarded_continuation import GUARD
R=0x80010000;L=0x80020000;N=0x60000000;BR=0x4e800420;W=0x80610000;D=R+400;S=R+304
class Test(unittest.TestCase):
    def setUp(self):
        rows=tuple((R+4*i,N) for i in range(76))
        acc=tuple((R+4*i,4,-48,True,True) for i in range(13))+tuple((R+4*(30+i),4,0x80030000+4*i,False,False) for i in range(5))+((R+240,4,-8,True,False),)
        known=tuple((pc,at,b'abcd') for pc,n,at,s,w in acc if not s)
        slots=((4,32),(-4,14),(-8,15),(-12,16))
        self.old=({R:(N,)*76+(BR,)+(GUARD,)*23+(N,GUARD)},(R,L,S,BR,48,0,0,D,N,383*4),rows,acc,slots,known)
        self.new=[{R:(N,)*76+(BR,)+(GUARD,)*23+(N,)*7+(W,GUARD)},(R,L,D+28,W,48,-20,4),rows+((S,BR),)+tuple((D+4*i,N) for i in range(7)),acc+((D+4,4,-16,True,False),(D+8,4,-12,True,False)),slots,known]
    def test_exact(self):self.assertEqual(compare(self.old,self.new),self.new)
    def test_edge(self):
        self.new[2]=self.new[2][:77]+((D+4,N),)+self.new[2][78:]
        with self.assertRaisesRegex(ValueError,'prefix'):compare(self.old,self.new)
    def test_boundary(self):
        self.new[1]=self.new[1][:5]+(0,4)
        with self.assertRaisesRegex(ValueError,'boundary'):compare(self.old,self.new)
    def test_access(self):
        self.new[3]=self.new[3][1:]+((D,4,-8,True,False),)
        with self.assertRaisesRegex(ValueError,'access'):compare(self.old,self.new)
    def test_old_word(self):
        self.new[0][R]=(BR,)+self.new[0][R][1:]
        with self.assertRaisesRegex(ValueError,'old words'):compare(self.old,self.new)
if __name__=='__main__':unittest.main(verbosity=2)
