#!/usr/bin/env python3
"""Original-free regression for the authenticated 127 nested fixture join."""
import unittest
from pathlib import Path
from audit_formatter_report_fifth_immediate_successor import Tests as AuditInputs
from guarded_continuation import GUARD
from prepare_formatter_nested_fixture import sixth_immediate_extension
from prepare_formatter_report_sixth_immediate_fixture import promote, render

NOOP = 0x60000000
SIBLING = 0x80030000


class SixthNestedTests(unittest.TestCase):
    def setUp(self):
        self.audit = AuditInputs(
            'test_instruction_126_constant_reaches_next_original_input')
        self.audit.setUp()
        self.parents = self.audit.inputs(
            next_word=(14 << 26) | (5 << 21) | 0xff80)
        self.fifth = self.parents[0]
        self.sixth = promote(*self.parents, NOOP)
        self.old = {**self.fifth[0], SIBLING: (NOOP, GUARD)}
        self.root = self.fifth[1][0]

    def test_exact_join_and_unmodified_siblings(self):
        merged, fields = sixth_immediate_extension(
            self.old, self.fifth, self.sixth)
        self.assertEqual(len(self.old[self.root]), 11)
        self.assertEqual(len(merged[self.root]), 12)
        self.assertEqual(merged[self.root], self.old[self.root][:-1] +
                         (NOOP, GUARD))
        self.assertEqual(fields, self.sixth[1])
        self.assertEqual(fields[1], self.root+36)
        self.assertEqual(fields[3], self.root+40)
        self.assertEqual(fields[5:7], (5, 0xffffff80))
        self.assertEqual(merged[SIBLING], (NOOP, GUARD))
        self.assertIn('formatter_report_sixth_immediate_private',
                      render(self.sixth))

    def test_mutated_guard_sibling_and_predecessors_refuse(self):
        old = self.old
        variants = [
            ({**old, self.root: old[self.root][:-1] + (0,)},
             self.fifth, self.sixth),
            ({**old, self.root+4: (NOOP, GUARD)},
             self.fifth, self.sixth),
            (old, None, self.sixth),
            (old, self.parents[1], self.sixth),
            (old, self.fifth, None),
        ]
        for prior, fifth, sixth in variants:
            with self.subTest(case=(type(fifth).__name__,
                                    type(sixth).__name__, len(prior))):
                with self.assertRaises(ValueError):
                    sixth_immediate_extension(prior, fifth, sixth)
        blocks, fields = self.sixth
        for bad in (
            ({**blocks, self.root: blocks[self.root][:-1]+(0,)}, fields),
            (blocks, fields[:4]+(GUARD,)+fields[5:]),
            (blocks, fields[:-1]+(self.root+44,)),
        ):
            with self.assertRaises(ValueError):
                sixth_immediate_extension(self.old, self.fifth, bad)

    def test_fixture_expansion_and_cli_stay_opt_in(self):
        s = Path(__file__).with_name(
            'prepare_formatter_nested_fixture.py').read_text()
        markers = (
            'sixth_immediate_extension(expanded,fifth_immediate_contract,sixth_immediate_contract)',
            'sixth_immediate_extension(final,fifth_immediate_contract,sixth_immediate_contract)',
            'extent=48 if sixth_immediate_contract is not None',
            'render_report_sixth_immediate(sixth_immediate_contract)',
            'sixth_immediate_contract=report_sixth_immediate_plan(',
            'if q.caller_report_sixth_immediate:q.caller_report_fifth_immediate=True',
            "modes.add_argument('--caller-report-sixth-immediate',action='store_true')",
            'sixth_immediate_contract=sixth_immediate_contract',
        )
        for marker in markers:
            with self.subTest(marker=marker):
                self.assertIn(marker, s)


if __name__ == '__main__':
    unittest.main(verbosity=2)
