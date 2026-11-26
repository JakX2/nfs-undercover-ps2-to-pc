#!/usr/bin/env python3
import unittest
from prepare_formatter_continuation_plan import contract
from guarded_continuation import GUARD
R=0x80001000;T=0x80002000;L=0x80003000;N=0x60000000
def bl(a,b):return 0x48000001|((b-a)&0x03fffffc)
class Tests(unittest.TestCase):
    def setUp(self):
        slots=((4,32),)+tuple((4*(i-32),i) for i in range(16,32))
        self.prior=((None,None,None,(R,),None,None,slots),None,{R:(N,GUARD),L:(N,)},(L,R+4,GUARD))
        self.words=(N,)*10+(bl(R+40,T),N)
        self.active=tuple(R+4*i for i in range(1,11))
        self.gp=[('reg',i) for i in range(32)]
        self.gp[3]=('const',1)
        for i in (4,5,6):self.gp[i]=('stack',-100-i*4)
    def result(self,sites=(),frame=704,saves=16):
        return self.active,frame,sites,saves,T,self.gp,{},()
    def test_contract(self):
        blocks,root,start,dst,w,rows,mask,args=contract(self.prior,R,self.words,self.result(),N)
        self.assertEqual((root,start,dst,w),(R,R+4,T,N))
        self.assertEqual((len(rows),mask.bit_count(),len(args)),(10,16,4))
        self.assertEqual(blocks[R][-1],GUARD)
        self.assertEqual(blocks[T],(N,GUARD))
    def test_memory_refusal(self):
        with self.assertRaisesRegex(ValueError,'contract'):
            contract(self.prior,R,self.words,self.result(sites=((R,'read',4,0),)),N)
    def test_frame_refusal(self):
        with self.assertRaisesRegex(ValueError,'contract'):
            contract(self.prior,R,self.words,self.result(frame=48),N)
    def test_arguments_refusal(self):
        self.gp[6]=('reg',6)
        with self.assertRaisesRegex(ValueError,'arguments'):
            contract(self.prior,R,self.words,self.result(),N)
if __name__=='__main__':unittest.main(verbosity=2)
