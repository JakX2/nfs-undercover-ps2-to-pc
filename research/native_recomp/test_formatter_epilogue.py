#!/usr/bin/env python3
import unittest
from audit_formatter_epilogue import classify_next
def d(op,rt,ra,imm=0):return (op<<26)|(rt<<21)|(ra<<16)|(imm&0xffff)
class Epilogue(unittest.TestCase):
    def setUp(self):
        self.g=[('reg',r) for r in range(32)];self.g[1]=('stack',-912)
    def test_exact(self):self.assertEqual(classify_next(d(14,1,1,48),self.g,48),('add_immediate',1,1,0,1,0,0))
    def test_other(self):
        for w in (d(14,1,1,44),d(14,1,2,48),d(14,2,1,48),d(15,1,1,48),d(14,1,1,-48)):
            self.assertEqual(classify_next(w,self.g,48)[1],0)
    def test_unproven(self):
        self.g[1]=('reg',1)
        with self.assertRaisesRegex(ValueError,'state'):classify_next(d(14,1,1,48),self.g,48)
if __name__=='__main__':unittest.main(verbosity=2)
