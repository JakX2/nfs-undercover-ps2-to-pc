import unittest
from audit_transfer_abi_liveness_v1042 import analyze,effect,BLR
R=0x80004000
L=R+0x100
def d(op,t,a=0,imm=0):return op<<26|t<<21|a<<16|(imm&0xffff)
def x(t,a,b,xo):return 31<<26|t<<21|a<<16|b<<11|xo<<1
def bl(pc,target):return 0x48000001|((target-pc)&0x03fffffc)
class Liveness(unittest.TestCase):
    def test_reads_writes(self):
        self.assertEqual(effect(d(14,9)),(set(),{9}))
        self.assertEqual(effect(d(32,9,10)),({10},{9}))
        self.assertEqual(effect(d(36,9,1)),({1,9},set()))
        self.assertEqual(effect(x(9,10,9,444)),({9},{10}))
        self.assertEqual(effect(d(46,8,1)),({1},set(range(8,32))))
        self.assertIsNone(effect(0))
    def test_both_paths(self):
        # Conditional branch skips the first definition. Both paths must
        # overwrite r9 before the later read to establish independence.
        bc=0x41820008
        yes=analyze({R:[bc,d(14,9),d(14,9),d(14,10),d(36,9,1),BLR]},R,[])
        self.assertTrue(yes[0])
        no=analyze({R:[bc,d(14,9),d(36,9,1),d(14,10),BLR]},R,[])
        self.assertFalse(no[0]);self.assertEqual(no[-1],1)
    def test_callee_is_not_assumed_to_clobber(self):
        roots={R:[bl(R,L),d(36,9,1),BLR],L:[d(14,9),BLR]}
        self.assertTrue(analyze(roots,R,[(R,L)])[0])
        roots[L]=[BLR]
        self.assertEqual(analyze(roots,R,[(R,L)])[-1],1)
        roots[L]=[d(36,10,1),BLR]
        self.assertEqual(analyze(roots,R,[(R,L)])[-1],2)
    def test_unknown_and_return(self):
        self.assertFalse(analyze({R:[0,BLR]},R,[])[0])
        self.assertTrue(analyze({R:[BLR]},R,[])[0])
        self.assertTrue(analyze({R:[d(14,9),d(14,10),0,BLR]},R,[])[0])
        self.assertFalse(analyze({R:[bl(R,L),BLR],L:[BLR]},R,[])[0])
        with self.assertRaises(ValueError):analyze({R:[BLR]},R,[(R,R)])
if __name__=='__main__':unittest.main()
