import unittest
from audit_formatter_third_cell import classify
A=0x80010000;B=0x80020000;C=0x80030000
class Test(unittest.TestCase):
    def setUp(self):
        self.record=('writable',4,1,1,0,0,0);self.cells=((A,b'abcd'),(B,b'1234'))
    def test_candidate(self):self.assertEqual(classify(self.record,b'0000',C,self.cells,())[-2:],(0,1))
    def test_protected(self):self.assertEqual(classify(self.record,b'0000',C,self.cells,((C+3,4),))[-2:],(1,0))
    def test_writer(self):self.assertEqual(classify(self.record[:-1]+(1,),b'0000',C,self.cells,())[-1],0)
    def test_mismatch(self):self.assertEqual(classify(('writable',4,1,0,0,0,0),b'0000',C,self.cells,())[-1],0)
    def test_overlap(self):
        with self.assertRaisesRegex(ValueError,'overlap'):classify(self.record,b'0000',A,self.cells,())
    def test_alignment(self):
        with self.assertRaisesRegex(ValueError,'geometry'):classify(self.record,b'0000',C+1,self.cells,())
if __name__=='__main__':unittest.main(verbosity=2)
