#!/usr/bin/env python3
"""Original-free integration gates for nested instruction-122 fixture wiring."""
import unittest
from pathlib import Path

from audit_formatter_report_immediate_successor import Tests as AuditInputs
from guarded_continuation import GUARD
from prepare_formatter_nested_fixture import signext_extension
from prepare_formatter_report_signext_fixture import (
    promote as promote_signext, render as render_signext,
)

ROOT_SIBLING = 0x80030000
NOOP = 0x60000000


def extsb(reg=3):
    return (31 << 26) | (reg << 21) | (reg << 16) | (954 << 1)


class NestedSignextTests(unittest.TestCase):
    def setUp(self):
        base = AuditInputs('test_constant_written_by_121_is_symbolic_input_to_122')
        base.setUp()
        self.base = base
        self.immediate, self.copy, self.predecessor, self.compare = base.inputs(extsb())
        self.signext = promote_signext(self.immediate, self.copy,
                                       self.predecessor, self.compare, NOOP)
        self.old = {**self.immediate[0], ROOT_SIBLING: (NOOP, GUARD)}

    def test_exact_extension_with_sibling_and_previous_guard(self):
        merged, info = signext_extension(
            self.old, self.immediate, self.signext)
        root = self.base.root
        self.assertEqual(info, self.signext[1])
        self.assertEqual(merged[root], (
            self.base.load, self.base.cmp, self.base.copy_word,
            self.base.imm, extsb(), NOOP, GUARD))
        self.assertEqual(merged[ROOT_SIBLING], (NOOP, GUARD))
        self.assertEqual(self.old[root][-1], GUARD)
        self.assertEqual(self.immediate[0][root][-1], GUARD)
        self.assertEqual(len(merged), 2)
        self.assertIn('formatter_report_signext_private',
                      render_signext(self.signext))

    def test_mutated_predecessor_and_sibling_are_rejected(self):
        root = self.base.root
        bad_history = {**self.old, root: self.old[root][:-2] + (NOOP, GUARD)}
        with self.assertRaisesRegex(ValueError, 'signext predecessor'):
            signext_extension(bad_history, self.immediate, self.signext)
        bad_contract = (
            {**self.signext[0], ROOT_SIBLING: (NOOP, GUARD)},
            self.signext[1],
        )
        with self.assertRaisesRegex(ValueError, 'signext predecessor'):
            signext_extension(self.old, self.immediate, bad_contract)
        bad_contract = (
            {**self.signext[0], root: self.signext[0][root][:-2] +
             (extsb(), GUARD)},
            self.signext[1],
        )
        with self.assertRaisesRegex(ValueError, 'signext predecessor'):
            signext_extension(self.old, self.immediate, bad_contract)
        wrong = self.signext[1][:7] + (0,) + self.signext[1][8:]
        with self.assertRaisesRegex(ValueError, 'signext rendering'):
            signext_extension(self.old, self.immediate, (self.signext[0], wrong))

    def test_full_fixture_cli_and_scope_install_wired(self):
        source = Path(__file__).with_name(
            'prepare_formatter_nested_fixture.py').read_text()
        expected = (
            "modes.add_argument('--caller-report-signext',action='store_true')",
            'if q.caller_report_signext:q.caller_report_immediate=True',
            'signext_contract=report_signext_plan(',
            'signext_extension(expanded,immediate_contract,signext_contract)',
            'signext_extension(final,immediate_contract,signext_contract)',
            'extent=28 if signext_contract is not None else 24 if immediate_contract is not None',
            'render_report_signext(signext_contract)',
            'expected[si[3]]=(si[0],si[4])',
            'immediate_contract=immediate_contract,signext_contract=signext_contract',
        )
        for fragment in expected:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, source)
        self.assertEqual(source.count(
            "if signext_contract is not None and immediate_contract is None:"
            "raise ValueError('nested fixture mode')"), 3)
        self.assertEqual(source.count(
            'immediate_contract=immediate_contract,signext_contract=signext_contract'),
            3)


if __name__ == '__main__':
    unittest.main()
