#!/usr/bin/env python3
import unittest
from analyze_formatter_nested_path import candidate_map
from analyze_formatter_two_cell_path import second_cell,check_reads
R=0x80010000;A=0x80020000;B=0x80030000
class Test(unittest.TestCase):
    def setUp(self):
        self.cells=((A,b'abcd'),(B,b'1234'));self.path=tuple(R+4*i for i in range(46))
        self.sites=((self.path[35],'const_read',4,A),(self.path[44],'const_read',4,B))
    def test_map(self):
        self.assertEqual(candidate_map(None,self.cells),{(A,4):b'abcd',(B,4):b'1234'})
        self.assertEqual(candidate_map(self.cells[0],()),{(A,4):b'abcd'})
        for rows in ((self.cells[0],self.cells[0]),((A+1,b'abcd'),),((A,b'a'),)):
            with self.assertRaisesRegex(ValueError,'geometry'):candidate_map(None,rows)
        with self.assertRaisesRegex(ValueError,'cap'):candidate_map(None,self.cells+((B+4,b'xxxx'),))
        with self.assertRaisesRegex(ValueError,'modes'):candidate_map(self.cells[0],self.cells)
    def test_cell(self):
        self.assertEqual(second_cell(self.cells[0],B,b'1234',((B+4,4),)),self.cells)
        with self.assertRaisesRegex(ValueError,'protected'):second_cell(self.cells[0],B,b'1234',((B+3,4),))
    def test_reads(self):
        self.assertEqual(check_reads(self.cells,self.sites,self.path),[self.path[35],self.path[44]])
        with self.assertRaisesRegex(ValueError,'identity'):check_reads(self.cells,self.sites[:1],self.path)
        with self.assertRaisesRegex(ValueError,'identity'):check_reads(self.cells,self.sites+self.sites[:1],self.path)
        with self.assertRaisesRegex(ValueError,'order'):check_reads(self.cells,self.sites,tuple(reversed(self.path)))
if __name__=='__main__':unittest.main(verbosity=2)
