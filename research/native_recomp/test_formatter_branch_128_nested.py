#!/usr/bin/env python3
"""Original-free selected-target join tests for original-128 AOT planning."""
import unittest
from prepare_formatter_branch_128_fixture import Tests as Base, promote
from prepare_formatter_nested_fixture import branch_128_extension


class Branch128NativeFixtureJoin(unittest.TestCase):
    def setUp(self):
        self.base = Base('test_selected_and_untaken_edges_are_strictly_guarded')

    def test_selected_target_is_one_new_root(self):
        sixth, compare, words, size = self.base.inputs(eq=True)
        private = promote(sixth, compare, words, size)
        merged, info = branch_128_extension(sixth[0], sixth, private)
        selected = info[3]
        self.assertEqual(set(merged) - set(sixth[0]), {selected})
        self.assertEqual(merged[selected], (info[4], 0x44000002))
        self.assertEqual(merged[sixth[1][0]], sixth[0][sixth[1][0]])
        self.assertEqual(info[6], 1)

    def test_refuse_fallthrough_and_forged_target(self):
        sixth, compare, words, size = self.base.inputs(eq=False)
        fallthrough = promote(sixth, compare, words, size)
        with self.assertRaises(ValueError):
            branch_128_extension(sixth[0], sixth, fallthrough)
        sixth, compare, words, size = self.base.inputs(eq=True)
        private = promote(sixth, compare, words, size)
        blocks, info = private
        for slot, value in ((3, info[3]+4), (4, info[4]^1),
                            (5, info[5]+4), (6, 0), (7, 48)):
            with self.subTest(field=slot):
                bad = info[:slot] + (value,) + info[slot+1:]
                with self.assertRaises(ValueError):
                    branch_128_extension(sixth[0], sixth, (blocks, bad))
        prior = dict(sixth[0])
        prior[info[3]] = (info[4], 0x44000002)
        with self.assertRaises(ValueError):
            branch_128_extension(prior, sixth, private)
        with self.assertRaises(ValueError):
            branch_128_extension(sixth[0], sixth,
                                  ({**blocks, info[3]:(0x44000002,)}, info))


if __name__ == '__main__':
    unittest.main(verbosity=2)
