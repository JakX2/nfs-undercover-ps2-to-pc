import unittest
from analyze_formatter_three_cell_path import admitted,validate
from analyze_formatter_nested_path import candidate_map
R=0x80010000;A=0x80020000;B=0x80030000;C=0x80040000
class Test(unittest.TestCase):
    def setUp(self):
        self.audit=('writable',4,1,1,0,0,0,0,1)
        self.cells=((A,b'abcd'),(B,b'1234'),(C,b'5678'))
        self.path=tuple(R+4*i for i in range(80))
        self.old=self.path[:74]
        self.sites=tuple((self.path[i],'stack_write',1,-48+i) for i in range(16))+((self.path[35],'const_read',4,A),(self.path[44],'const_read',4,B),(self.path[74],'const_read',4,C))
    def test_admit(self):
        self.assertEqual(admitted(self.audit,C,b'5678',self.cells[:2]),self.cells)
        with self.assertRaisesRegex(ValueError,'cap'):candidate_map(None,self.cells)
        with self.assertRaisesRegex(ValueError,'cap'):candidate_map(None,self.cells[:2],third=True)
    def test_audit(self):
        with self.assertRaisesRegex(ValueError,'audit'):admitted(self.audit[:-1]+(0,),C,b'5678',self.cells[:2])
    def test_duplicate(self):
        with self.assertRaisesRegex(ValueError,'geometry'):admitted(self.audit,A,b'5678',self.cells[:2])
    def test_exact(self):self.assertEqual(validate(self.path,self.sites,self.old,self.sites[:18],self.cells),(80,80))
    def test_prefix(self):
        with self.assertRaisesRegex(ValueError,'prefix'):validate(self.path[1:],self.sites,self.old,self.sites[:18],self.cells)
    def test_read(self):
        with self.assertRaisesRegex(ValueError,'order'):validate(self.path,self.sites[:-1],self.old,self.sites[:18],self.cells)
if __name__=='__main__':unittest.main(verbosity=2)
