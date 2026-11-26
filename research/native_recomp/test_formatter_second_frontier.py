#!/usr/bin/env python3
import unittest
from analyze_formatter_second_frontier import summarize
R=0x80010000;A=0x80020000;B=0x80030000
class Test(unittest.TestCase):
    def setUp(self):
        self.path=tuple(R+4*i for i in range(40))
        self.cell=(A,b'abcd')
        self.record=[B,4,self.path,48,((self.path[35],'const_read',4,A),),[('stack',-48) if i==1 else ('reg',i) for i in range(32)],{}, {},None,None,frozenset()]
    def test_exact(self):
        self.assertEqual(summarize(self.cell,self.record)[:4],(39,39,4,48))
    def test_overlap(self):
        self.record[0]=A
        with self.assertRaisesRegex(ValueError,'overlap'):summarize(self.cell,self.record)
    def test_unresolved_site(self):
        self.record[4]+=((self.path[-1],'const_read',4,B),)
        with self.assertRaisesRegex(ValueError,'unresolved'):summarize(self.cell,self.record)
    def test_wrong_predecessor(self):
        self.record[4]=((self.path[34],'const_read',4,A),)
        with self.assertRaisesRegex(ValueError,'predecessor'):summarize(self.cell,self.record)
if __name__=='__main__':unittest.main(verbosity=2)
