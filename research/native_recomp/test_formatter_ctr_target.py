import unittest
from audit_formatter_ctr_target import geometry
R=0x80010000;T=0x80020000
class Test(unittest.TestCase):
    def setUp(self):self.s={R:383*4,T:16}
    def test_local(self):
        self.assertEqual(geometry(R,R,self.s),('local_entry',1))
        self.assertEqual(geometry(R,R+12,self.s),('local_interior',1))
    def test_other(self):
        self.assertEqual(geometry(R,T,self.s),('function_entry',1))
        self.assertEqual(geometry(R,T+4,self.s),('function_interior',1))
        self.assertEqual(geometry(R,T+16,self.s),('no_symbol',0))
    def test_invalid(self):
        self.assertEqual(geometry(R,None,self.s),('unknown',0))
        self.assertEqual(geometry(R,R+1,self.s),('unaligned',0))
        self.assertEqual(geometry(R,0,self.s),('outside_mem1',0))
        with self.assertRaisesRegex(ValueError,'owner size'):geometry(R,R,{R:4})
    def test_ambiguous(self):
        self.assertEqual(geometry(R,T+4,{**self.s,T+4:8}),('ambiguous',2))
if __name__=='__main__':unittest.main(verbosity=2)
