import unittest
from analyze_formatter_after_ctr import verify_path
R=0x80010000
class Test(unittest.TestCase):
    def setUp(self):
        self.prior=tuple(R+4*i for i in range(77))
        self.dst=R+0x200;self.edge=(self.prior[-1],self.dst)
        self.sites=tuple((self.prior[i],'stack_write',1,-48+i) for i in range(19))
        self.path=self.prior+(self.dst,self.dst+4)
    def test_exact(self):self.assertEqual(verify_path(self.path,self.sites,self.prior,self.sites,self.edge),(79,79))
    def test_wrong_target(self):
        with self.assertRaisesRegex(ValueError,'prefix'):verify_path(self.prior+(self.dst+4,),self.sites,self.prior,self.sites,self.edge)
    def test_missing_access(self):
        with self.assertRaisesRegex(ValueError,'accesses'):verify_path(self.path,self.sites[1:],self.prior,self.sites,self.edge)
    def test_repeated(self):
        with self.assertRaisesRegex(ValueError,'repeated'):verify_path(self.path+(self.edge[0],),self.sites,self.prior,self.sites,self.edge)
if __name__=='__main__':unittest.main(verbosity=2)
