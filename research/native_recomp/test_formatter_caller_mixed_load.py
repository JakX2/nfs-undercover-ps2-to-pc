#!/usr/bin/env python3
import unittest
from audit_formatter_caller_mixed_load import audit
P=0x80010000;SP=-864;N=0x60000000;LOAD=0x80610010
class MixedLoad(unittest.TestCase):
    def setUp(self):
        # Synthetic rows exercise census/boundary checks. The actual row
        # semantics are authenticated by the private mixed contract.
        self.rows=((P,N,(),P+4,None,None),(P+4,N,(),P+8, P+24,False),
                   (P+8,N,(),P+12,None,None),(P+12,N,(),P+16,P+28,True),
                   (P+16,N,(),P+20,P+32,True))
        self.contract=({P:(N,)*5+(LOAD,)},self.rows,P+20,LOAD)
        self.live=[('reg',r) for r in range(32)];self.live[1]=('stack',SP)
        self.initial=tuple(self.live);self.mem={SP+16+i:('byte',i) for i in range(4)}
    def probe(self):return audit(self.contract,self.live,self.mem,self.initial,{},((0,SP+16,4,'const'),))
    def test_exact(self):self.assertEqual(self.probe(),('parent',4,0,4,4,0,'const','volatile',0))
    def test_partial(self):
        self.mem[SP+18]=('uninitialized',SP-38);self.mem[SP+19]=('uninitialized',SP-37)
        self.assertEqual(self.probe()[5:7],(2,'partial'))
    def test_count(self):
        self.contract=(self.contract[0],self.rows[:-1],*self.contract[2:])
        with self.assertRaisesRegex(ValueError,'predecessor'):self.probe()
    def test_boundary(self):
        self.contract=({P:(N,)*6},*self.contract[1:])
        with self.assertRaisesRegex(ValueError,'boundary'):self.probe()
    def test_released_stack(self):
        self.live[1]=('stack',SP-48)
        with self.assertRaisesRegex(ValueError,'state'):self.probe()
if __name__=='__main__':unittest.main(verbosity=2)
