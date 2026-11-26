#!/usr/bin/env python3
import unittest
from analyze_formatter_next_dependency import census
R=0x80001000;T=0x80002000;N=0x60000000;RET=0x4e800020
def b(a,z,lk=False):return 0x48000000|((z-a)&0x03fffffc)|int(lk)
def bc(a,z,bo=12,lk=False):return 0x40000000|(bo<<21)|((z-a)&0xfffc)|int(lk)
class Test(unittest.TestCase):
    def test_direct_call_boundary(self):
        ws=(N,b(R+4,T,True),N,RET)
        f=census(R,ws,stop_at_calls=True);g=census(R,ws,stop_at_calls=False)
        self.assertEqual((f['visited'],g['visited'],len(g['calls'])),(2,4,1))
        self.assertEqual(g['boundaries'],{'direct_call':1,'return':1})
    def test_conditional_call_fallthrough(self):
        ws=(bc(R,T,lk=True),RET)
        self.assertEqual(census(R,ws,stop_at_calls=True)['visited'],2)
    def test_conditional_return(self):
        ws=(0x4d820020,N,RET)
        self.assertEqual(census(R,ws,stop_at_calls=True)['boundaries'],{'return':2})
    def test_loop(self):
        ws=(N,bc(R+4,R,bo=16),RET)
        q=census(R,ws,stop_at_calls=False)
        self.assertEqual((q['visited'],q['backedges']),(3,1))
    def test_unconditional_tail(self):
        self.assertEqual(census(R,(b(R,T),),stop_at_calls=False)['boundaries'],{'direct_tail':1})
    def test_indirect_call(self):
        ws=(0x4e800421,RET)
        self.assertEqual(census(R,ws,stop_at_calls=True)['visited'],1)
        self.assertEqual(census(R,ws,stop_at_calls=False)['boundaries'],{'indirect_call':1,'return':1})
    def test_invalid(self):
        for ws in ((N,),(b(R,R+4,True),RET),(0x48000002,),(b(R,R),)):
            with self.assertRaises(ValueError):census(R,ws,stop_at_calls=False)
if __name__=='__main__':unittest.main(verbosity=2)
