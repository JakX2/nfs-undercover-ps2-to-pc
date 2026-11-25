import unittest
from audit_si_deep_v695 import census,region,call_kind
H=0x80004000
class Tests(unittest.TestCase):
    def test_static_si(self):
        # lis r3,0xcd00; ori r3,r3,0x6400; lwz r4,0x34(r3); stw r4,0x38(r3); blr
        out,first=census(H,[0x3c60cd00,0x60636400,0x80830034,0x90830038,0x4e800020])
        self.assertEqual((out['read_si_control'],out['write_si_status'],first),(1,1,()))
        self.assertEqual(region(0xcd806434),'si_control')
        self.assertEqual(region(0x4d006434),'memory')
    def test_unknown_and_join(self):
        # Unknown instruction invalidates constants, so no false MMIO identity.
        out,_=census(H,[0x3c60cd00,0x60636400,0x7c000000,0x90830034,0x4e800020])
        self.assertEqual((out['write_si_control'],out['write_unknown']),(0,1))
        # A conditional branch skips the address initialization.
        out,_=census(H,[0x4182000c,0x3c60cd00,0x60636400,0x90830034,0x4e800020])
        self.assertEqual((out['write_si_control'],out['write_unknown']),(0,1))
    def test_call_boundary(self):
        out,first=census(H,[0x3c60cd00,0x60636400,0x48000009,0x90830034,0x4e800020])
        self.assertEqual((out['write_si_control'],first),(0,(1,)))
        self.assertEqual(call_kind(0x4e800421),2)
        self.assertEqual(call_kind(0x4e800020),0)
if __name__=='__main__':unittest.main()
