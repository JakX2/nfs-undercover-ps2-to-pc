#!/usr/bin/env python3
import unittest
from prepare_post_stm_sc_report_formatter_path import first_path,const
from prepare_post_stm_sc_formatter_leaf_path import run
from prepare_post_stm_sc_formatter_resume_path import resume
R=0x80001000;T=0x80002000;N=0x80003000
def ins(op,rs,ra,n):return (op<<26)|(rs<<21)|(ra<<16)|(n&0xffff)
def bl(a,b):return 0x48000001|((b-a)&0x03fffffc)
def fixture(fault=False):
    return (ins(37,1,1,-32),0x7c0802a6,ins(36,0,1,36),ins(36,31,1,28),
        ins(14,3,0,1),ins(36,3,1,8),bl(R+24,T),
        ins(36,3,1,28 if fault else 8),ins(32,4,1,8),ins(11,0,4,2),
        0x40820008,bl(R+44,N),0x4e800020)
class Resume(unittest.TestCase):
    def get(self,ws):
        p=first_path(R,ws,{}, {},(),details=True)
        leaf=run(T,(ins(14,3,3,1),0x4e800020),p[5],(),p[6],initial_cr=p[7][2],details=True)
        return p,leaf
    def test_return_and_resume(self):
        ws=fixture();p,l=self.get(ws);q=resume(R,ws,p,l,())
        self.assertEqual((len(p[0]),len(l[0]),len(q[0]),q[4]),(7,2,5,N))
        self.assertEqual(q[5][4],const(2));self.assertEqual(q[1],32)
        self.assertEqual([x[1] for x in q[2]],['stack_write','stack_read'])
        self.assertEqual(q[7][2][2],True)
    def test_protected_slot(self):
        ws=fixture(True);p,l=self.get(ws)
        with self.assertRaisesRegex(ValueError,'protected stack'):resume(R,ws,p,l,())
    def test_leaf_abi(self):
        ws=fixture();p,l=self.get(ws);bad=list(l);gp=list(bad[5]);gp[31]=const(9);bad[5]=tuple(gp)
        with self.assertRaisesRegex(ValueError,'leaf ABI'):resume(R,ws,p,tuple(bad),())
if __name__=='__main__':unittest.main(verbosity=2)
