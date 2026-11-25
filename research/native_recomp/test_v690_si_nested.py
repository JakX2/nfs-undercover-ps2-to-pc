import unittest
from audit_si_nested_v690 import prefix,target
H=0x80004000
def b(a,t,link=False):return 0x48000000|((t-a)&0x03fffffc)|int(link)
def bc(a,t):return 0x41820000|((t-a)&0xfffc)
class Tests(unittest.TestCase):
    def test_linear_and_branch(self):
        w=[0x90030000,bc(H+4,H+16),b(H+8,H+0x100,True),0x4e800020,b(H+16,H+0x200,True),0x4e800020]
        self.assertEqual(prefix(H,w),dict(labels=4,stores=1,returns=0,outside=0,unknown=0,first_calls=(1,2)))
        self.assertEqual(target(H+4,bc(H+4,H)),H)
        self.assertEqual(target(H+8,b(H+8,H)),H)
    def test_loop_and_refusal(self):
        self.assertEqual(prefix(H,[bc(H,H),0x4e800020])['returns'],1)
        self.assertEqual(prefix(H,[b(H,H+64)])['outside'],1)
        self.assertEqual(prefix(H,[0x4c000064])['unknown'],1)
        self.assertEqual(prefix(H,[0x48000009,0x90030000,0x4e800020])['stores'],0)
        for bad in ([],[0]*1025):
            with self.assertRaises(ValueError):prefix(H,bad)
if __name__=='__main__':unittest.main()
