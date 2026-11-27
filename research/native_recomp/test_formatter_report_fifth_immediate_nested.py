#!/usr/bin/env python3
"""Source-only, mutation-heavy nested fixture join for original instruction 126.

All inputs synthetic. Authenticating a layout is not game-code execution.
"""
import unittest
from pathlib import Path

from audit_formatter_report_fourth_immediate_successor import Tests as AuditInputs
from guarded_continuation import GUARD
from prepare_formatter_nested_fixture import fifth_immediate_extension
from prepare_formatter_report_fifth_immediate_fixture import (
    promote as promote_fifth, render as render_fifth,
)

SIBLING = 0x80030000
NOOP = 0x60000000


class NestedFifthImmediateTests(unittest.TestCase):
    def setUp(self):
        self.audit = AuditInputs('test_instruction_125_result_reaches_126_input')
        self.audit.setUp()
        (self.fourth, self.third, self.second, self.signext, self.immediate,
         self.copy, self.predecessor, self.compare) = self.audit.inputs(
             next_word=self.audit.base.base.addi(5, 0, 0xff80))
        self.fifth = promote_fifth(
            self.fourth, self.third, self.second, self.signext,
            self.immediate, self.copy, self.predecessor, self.compare, NOOP)
        self.old = {**self.fourth[0], SIBLING: (NOOP, GUARD)}

    @property
    def root(self):
        return self.audit.base.base.base.root

    def test_exact_126_layout_preserves_sibling(self):
        merged, info = fifth_immediate_extension(
            self.old, self.fourth, self.fifth)
        self.assertEqual(info, self.fifth[1])
        self.assertEqual(len(self.old[self.root]), 10)
        self.assertEqual(len(merged[self.root]), 11)
        self.assertEqual(
            merged[self.root], self.old[self.root][:-1] + (NOOP, GUARD))
        self.assertEqual(merged[SIBLING], (NOOP, GUARD))
        self.assertEqual(info[1:5], (
            self.root + 32, self.audit.base.base.addi(5, 0, 0xff80),
            self.root + 36, NOOP))
        self.assertEqual(info[5:7], (5, 0xffffff80))
        self.assertIn('formatter_report_fifth_immediate_private',
                      render_fifth(self.fifth))

    def test_signed_extremes_and_volatile_destinations(self):
        for dst in (0, 3, 5, 12):
            for imm, value in ((0, 0), (0x7fff, 0x7fff),
                               (0x8000, 0xffff8000),
                               (0xffff, 0xffffffff)):
                with self.subTest(dst=dst, imm=imm):
                    ancestors = self.audit.inputs(
                        next_word=self.audit.base.base.addi(dst, 0, imm))
                    candidate = promote_fifth(*ancestors, NOOP)
                    prior = {**ancestors[0][0], SIBLING: (NOOP, GUARD)}
                    merged, info = fifth_immediate_extension(
                        prior, ancestors[0], candidate)
                    self.assertEqual(info[5:7], (dst, value))
                    self.assertEqual(merged[self.root][-3:],
                                     (self.audit.base.base.addi(dst, 0, imm),
                                      NOOP, GUARD))
                    self.assertEqual(merged[SIBLING], (NOOP, GUARD))

    def test_mutated_predecessor_and_guard_fail_closed(self):
        r = self.root
        before = self.old[r]
        corrupt = (
            {**self.old, r: before[:-1] + (0,)},
            {**self.old, r: before[:8] + (0,) + before[9:]},
            {**self.old, r: before[:9] + (NOOP,)},
            {**self.old, r + 4: (NOOP, GUARD)},
        )
        for p in corrupt:
            with self.subTest(root_count=len(p)):
                with self.assertRaises(ValueError):
                    fifth_immediate_extension(p, self.fourth, self.fifth)
        blocks, fields = self.fifth
        corrupt_fifth = (
            ({**blocks, r: blocks[r][:-1] + (0,)}, fields),
            (blocks, fields[:4] + (GUARD,) + fields[5:]),
            (blocks, fields[:5] + (0,) + fields[6:]),
            (blocks, fields[:-1] + (r + 40,)),
            ({**blocks, SIBLING: (NOOP, GUARD)}, fields),
        )
        for candidate in corrupt_fifth:
            with self.subTest(fields=candidate[1]):
                with self.assertRaises(ValueError):
                    fifth_immediate_extension(self.old, self.fourth, candidate)

    def test_missing_predecessor_overlap_and_sibling(self):
        for ancestor in (None, self.third, self.second):
            with self.subTest(ancestor=type(ancestor).__name__):
                with self.assertRaises(ValueError):
                    fifth_immediate_extension(self.old, ancestor, self.fifth)
        with self.assertRaises(ValueError):
            fifth_immediate_extension(
                {**self.old, self.root + 4: (NOOP, GUARD)},
                self.fourth, self.fifth)
        changed = {**self.old, SIBLING: (0, GUARD)}
        merged, _ = fifth_immediate_extension(
            changed, self.fourth, self.fifth)
        self.assertEqual(merged[SIBLING], (0, GUARD))

    def test_cli_scope_and_native_install_are_still_gated(self):
        source = Path(__file__).with_name(
            'prepare_formatter_nested_fixture.py').read_text()
        expected = (
            "modes.add_argument('--caller-report-fifth-immediate',action='store_true')",
            'if q.caller_report_fifth_immediate:q.caller_report_fourth_immediate=True',
            'fifth_immediate_contract=report_fifth_immediate_plan(',
            'fifth_immediate_extension(expanded,fourth_immediate_contract,fifth_immediate_contract)',
            'fifth_immediate_extension(final,fourth_immediate_contract,fifth_immediate_contract)',
            'else 44 if fifth_immediate_contract is not None',
            'render_report_fifth_immediate(fifth_immediate_contract)',
            'expected[wi[3]]=(wi[0],wi[4])',
            'fifth_immediate_contract=fifth_immediate_contract',
        )
        for marker in expected:
            with self.subTest(marker=marker):
                self.assertIn(marker, source)
        self.assertEqual(source.count(
            "if fifth_immediate_contract is not None and fourth_immediate_contract is None:"
            "raise ValueError('nested fixture mode')"), 3)
        self.assertEqual(source.count(
            "fourth_immediate_contract=fourth_immediate_contract,"
            "fifth_immediate_contract=fifth_immediate_contract"), 3)


if __name__ == '__main__':
    unittest.main(verbosity=2)
