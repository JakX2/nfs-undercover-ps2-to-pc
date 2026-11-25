import unittest
from audit_handler_frontier_v896 import region,paths
class Frontier(unittest.TestCase):
    def test_regions(self):
        regs=[None]*32;regs[3]=0xcd006400
        for off,label in ((0x34,'si_control'),(0x38,'si_status'),(0x30,'si_poll'),(0x80,'si_buffer')):
            self.assertEqual(region(0x80830000|off,regs),('load',label,32))
        regs[3]=0xc0000000
        self.assertEqual(region(0x80830000,regs),('load','mem1_uncached',32))
    def test_paths(self):
        h=0x80004000
        rows={h:(0x3c60cd00,0,0),h+4:(0x80836438,0,0)}
        self.assertEqual(paths(rows,h,2),[('load','si_status',32)])
if __name__=='__main__':unittest.main()
