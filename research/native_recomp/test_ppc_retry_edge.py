#!/usr/bin/env python3
"""Independent synthetic PPC retry branch regression tests."""
import unittest
from ppc_retry_edge import decode_bc, evaluate, classify_retry_window, sanitized

def bc(pc, target, bo, bi, absolute=False):
    delta = target if absolute else target-pc
    assert delta % 4 == 0 and -32768 <= delta <= 32764
    return (16<<26)|(bo<<21)|(bi<<16)|(delta & 0xfffc)|(2 if absolute else 0)

class RetryEdgeTests(unittest.TestCase):
    def test_cr_only_loop_and_exit(self):
        word=bc(0x1020,0x1000,12,2)
        edge=decode_bc(word)
        self.assertEqual((edge.cr_field,edge.cr_bit),(0,2))
        self.assertEqual(evaluate(edge,0x20000000,7),(True,7))
        self.assertEqual(evaluate(edge,0,7),(False,7))
        stats=classify_retry_window(0x1000,[0x60000000]*8+[word],0x1004)
        self.assertEqual(stats["back_span"],32)
        self.assertEqual(stats["cr_expected"],1)
        self.assertEqual(stats["ctr_decrement"],0)
        self.assertTrue(sanitized(stats).startswith("RETRY_EDGE backedge_count=1"))

    def test_ctr_only_loop(self):
        edge=decode_bc(bc(0x1020,0x1000,16,0))
        self.assertEqual(evaluate(edge,0,3),(True,2))
        self.assertEqual(evaluate(edge,0,1),(False,0))
        self.assertEqual(evaluate(edge,0,0),(True,0xffffffff))

    def test_combined_ctr_and_cr(self):
        edge=decode_bc(bc(0x1020,0x1000,0,6))
        self.assertEqual(evaluate(edge,0,3),(True,2))
        self.assertEqual(evaluate(edge,0x02000000,3),(False,2))

    def test_reject_invalid_or_ambiguous(self):
        with self.assertRaisesRegex(ValueError,"not_bc"):
            decode_bc(0x60000000)
        with self.assertRaisesRegex(ValueError,"register"):
            evaluate(decode_bc(bc(0x1020,0x1000,12,2)),-1,0)
        with self.assertRaisesRegex(ValueError,"ambiguous_backedge"):
            classify_retry_window(0x1000,[0x60000000]*10,0x1004)
        with self.assertRaisesRegex(ValueError,"ambiguous_backedge"):
            classify_retry_window(0x1000,[bc(0x1000,0x1000,12,2),
                bc(0x1004,0x1000,12,2)],0x1004)

if __name__=="__main__":
    unittest.main()
