import unittest
from analyze_formatter_after_ctr import verify_path,classify_stack
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
    def test_stack_region(self):
        for at,kind in ((-920,'below_frame'),(-912,'child_local'),(-864,'caller_linkage'),(-856,'caller_storage'),(8,'outside_parent')):
            self.assertEqual(classify_stack(at,4,-864,48,{at:1,at+1:2},{at:1}),(kind,2,1))
        with self.assertRaisesRegex(ValueError,'geometry'):classify_stack(-863,4,-864,48,{}, {})
    def test_cross_region(self):
        self.assertEqual(classify_stack(-912,4,-864,48,{},{}),('child_local',0,0))
if __name__=='__main__':unittest.main(verbosity=2)
