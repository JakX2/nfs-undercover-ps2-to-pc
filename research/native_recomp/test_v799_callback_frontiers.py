import unittest
from audit_callback_frontiers_v799 import call_sites, groups, continuations
from prepare_owner_leaf_v714 import bl

class Frontiers(unittest.TestCase):
    def test_shared_groups_and_indirect(self):
        r=0x80004000
        code=[bl(r,r+0x100),0x4e800421,bl(r+8,r+0x100),bl(r+12,r+0x200),0x4e800020]
        sites=call_sites(r,code)
        self.assertEqual(groups(sites),(1,0,1,2))
        rows=continuations(r,code)
        self.assertEqual([v[4] for v in rows],[(1,),(2,),(3,),(4,),()])
        self.assertEqual(rows[-1][5],(0,1,0,0))
    def test_branch_frontier(self):
        r=0x80004000
        code=[bl(r,r+0x100),0x4182000c,bl(r+8,r+0x200),0x48000008,
              bl(r+16,r+0x300),0x4e800020]
        rows=continuations(r,code)
        self.assertEqual(rows[1][4],(2,3))
        self.assertEqual(rows[2][4],())
        self.assertEqual(rows[2][5],(0,1,0,0))
    def test_refusals(self):
        for w in (0x48000003,0x41820005,0x4e800021):
            with self.assertRaises(ValueError):call_sites(0x80004000,[w])
        with self.assertRaises(ValueError):call_sites(0x80004001,[0x60000000])
        with self.assertRaises(ValueError):continuations(0x80004000,[0x60000000])

if __name__=='__main__':unittest.main()
