import unittest
from audit_handler_branch_frontier_v907 import frontier
class Frontier(unittest.TestCase):
    def test_boundaries(self):
        code=[0x60000000,0x60000000,0x48000001,0x60000000]
        self.assertEqual(frontier(0x80004000,code,0),(code[:2],(2,code[2])))
        self.assertEqual(frontier(0x80004000,code,2),([],(2,code[2])))
        with self.assertRaises(ValueError):frontier(0x80004000,code,3)
if __name__=='__main__':unittest.main()
