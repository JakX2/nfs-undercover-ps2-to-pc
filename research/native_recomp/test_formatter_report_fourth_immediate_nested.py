#!/usr/bin/env python3
"""Original-free integration and fail-closed tests of 125 fixture nesting."""
import unittest
from pathlib import Path

from audit_formatter_report_third_immediate_successor import Tests as AuditInputs
from guarded_continuation import GUARD
from prepare_formatter_nested_fixture import fourth_immediate_extension
from prepare_formatter_report_fourth_immediate_fixture import (
    promote as promote_fourth, render as render_fourth,
)

SIBLING = 0x80030000
NOOP = 0x60000000


class NestedFourthImmediateTests(unittest.TestCase):
    def setUp(self):
        self.audit = AuditInputs('test_instruction_124_result_reaches_next_input')
        self.audit.setUp()
        (self.third, self.second, self.signext, self.immediate,
         self.copy, self.predecessor, self.compare) = self.audit.inputs(
             next_word=self.audit.base.addi(5, 0, 0xff80))
        self.fourth = promote_fourth(
            self.third, self.second, self.signext, self.immediate,
            self.copy, self.predecessor, self.compare, NOOP)
        self.old = {**self.third[0], SIBLING: (NOOP, GUARD)}

    def test_exact_125_layout_preserves_sibling(self):
        root = self.audit.base.base.root
        merged, info = fourth_immediate_extension(
            self.old, self.third, self.fourth)
        self.assertEqual(info, self.fourth[1])
        self.assertEqual(len(self.old[root]), 9)
        self.assertEqual(len(merged[root]), 10)
        self.assertEqual(merged[root], self.old[root][:-1] + (NOOP, GUARD))
        self.assertEqual(merged[SIBLING], (NOOP, GUARD))
        self.assertEqual(info[1:5], (
            root + 28, self.audit.base.addi(5, 0, 0xff80),
            root + 32, NOOP))
        self.assertEqual(info[5:7], (5, 0xffffff80))
        self.assertIn('formatter_report_fourth_immediate_private',
                      render_fourth(self.fourth))

    def test_signed_extremes_and_valid_destinations(self):
        for dst in (0, 3, 5, 12):
            for imm, value in ((0, 0), (0x7fff, 0x7fff),
                               (0x8000, 0xffff8000),
                               (0xffff, 0xffffffff)):
                with self.subTest(dst=dst, imm=imm):
                    third, second, signext, immediate, copy, predecessor, compare = (
                        self.audit.inputs(next_word=self.audit.base.addi(
                            dst, 0, imm)))
                    fourth = promote_fourth(
                        third, second, signext, immediate, copy,
                        predecessor, compare, NOOP)
                    prior = {**third[0], SIBLING: (NOOP, GUARD)}
                    merged, info = fourth_immediate_extension(
                        prior, third, fourth)
                    self.assertEqual(info[5:7], (dst, value))
                    self.assertEqual(merged[self.audit.base.base.root][-3:],
                                     (self.audit.base.addi(dst, 0, imm),
                                      NOOP, GUARD))
                    self.assertEqual(merged[SIBLING], (NOOP, GUARD))

    def test_refuse_mutated_ancestor_word_and_moved_guards(self):
        root = self.audit.base.base.root
        oldroot = self.old[root]
        mutations = (
            {**self.old, root: oldroot[:-1] + (0,)},
            {**self.old, root: oldroot[:7] + (0,) + oldroot[8:]},
            {**self.old, root: oldroot[:8] + (NOOP,)},
            {**self.old, root + 4: (NOOP, GUARD)},
        )
        for before in mutations:
            with self.subTest(roots=tuple(before)):
                with self.assertRaises(ValueError):
                    fourth_immediate_extension(
                        before, self.third, self.fourth)
        blocks, fields = self.fourth
        altered = (
            ({**blocks, root: blocks[root][:-1] + (0,)}, fields),
            (blocks, fields[:4] + (GUARD,) + fields[5:]),
            (blocks, fields[:5] + (0,) + fields[6:]),
            (blocks, fields[:-1] + (root + 36,)),
            ({**blocks, SIBLING: (NOOP, GUARD)}, fields),
        )
        for candidate in altered:
            with self.subTest(info=candidate[1]):
                with self.assertRaises(ValueError):
                    fourth_immediate_extension(self.old, self.third, candidate)

    def test_reject_missing_predecessor_and_overlapping_root(self):
        with self.assertRaises(ValueError):
            fourth_immediate_extension(self.old, self.second, self.fourth)
        with self.assertRaises(ValueError):
            fourth_immediate_extension(self.old, None, self.fourth)
        with self.assertRaises(ValueError):
            fourth_immediate_extension(self.old, self.third, None)
        forged = {**self.old, self.audit.base.base.root + 4: (NOOP, GUARD)}
        with self.assertRaises(ValueError):
            fourth_immediate_extension(forged, self.third, self.fourth)
        changed = {**self.old, SIBLING: (0, GUARD)}
        merged, _ = fourth_immediate_extension(
            changed, self.third, self.fourth)
        self.assertEqual(merged[SIBLING], (0, GUARD))

    def test_cli_image_scope_and_native_install_checks_wired(self):
        source = Path(__file__).with_name(
            'prepare_formatter_nested_fixture.py').read_text()
        expected = (
            "modes.add_argument('--caller-report-fourth-immediate',action='store_true')",
            'if q.caller_report_fourth_immediate:q.caller_report_third_immediate=True',
            'fourth_immediate_contract=report_fourth_immediate_plan(',
            'fourth_immediate_extension(expanded,third_immediate_contract,fourth_immediate_contract)',
            'fourth_immediate_extension(final,third_immediate_contract,fourth_immediate_contract)',
            'extent=44 if fifth_immediate_contract is not None else 40 if fourth_immediate_contract is not None else 36',
            'render_report_fourth_immediate(fourth_immediate_contract)',
            'expected[vi[3]]=(vi[0],vi[4])',
            'fourth_immediate_contract=fourth_immediate_contract',
        )
        for marker in expected:
            with self.subTest(marker=marker):
                self.assertIn(marker, source)
        self.assertEqual(source.count(
            "if fourth_immediate_contract is not None and third_immediate_contract is None:"
            "raise ValueError('nested fixture mode')"), 3)
        self.assertEqual(source.count(
            'third_immediate_contract=third_immediate_contract,'
            'fourth_immediate_contract=fourth_immediate_contract'), 3)
        self.assertIn('nested fixture report fourth immediate predecessor', source)


if __name__ == '__main__':
    unittest.main(verbosity=2)
