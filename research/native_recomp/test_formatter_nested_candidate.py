#!/usr/bin/env python3
import unittest
from analyze_formatter_nested_candidate import admit
A=0x80010000
GOOD=('writable',4,1,1,0,0,0)
class Test(unittest.TestCase):
    def test_candidate(self):
        self.assertEqual(admit(GOOD,A,bytes(4),()),(A,bytes(4)))
    def test_audit_contract(self):
        for i,v in enumerate(('readonly',2,0,0,1,1,1)):
            q=list(GOOD);q[i]=v
            with self.assertRaisesRegex(ValueError,'audit contract'):admit(tuple(q),A,bytes(4),())
    def test_overlap(self):
        for a,n in ((A-4,5),(A+3,4),(A,4)):
            with self.assertRaisesRegex(ValueError,'protected overlap'):admit(GOOD,A,bytes(4),((a,n),))
        self.assertEqual(admit(GOOD,A,bytes(4),((A-4,4),(A+4,4)))[0],A)
    def test_range(self):
        for addr in (A+1,0x7ffffffc,0x81800000):
            with self.assertRaisesRegex(ValueError,'geometry'):admit(GOOD,addr,bytes(4),())
        with self.assertRaisesRegex(ValueError,'geometry'):admit(GOOD,A,bytes(3),())
if __name__=='__main__':unittest.main(verbosity=2)
