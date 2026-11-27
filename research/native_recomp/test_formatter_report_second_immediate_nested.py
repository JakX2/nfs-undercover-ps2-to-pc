#!/usr/bin/env python3
"""Original-free integration and fail-closed tests of 123 fixture nesting."""
import unittest
from pathlib import Path

from audit_formatter_report_immediate_successor import Tests as AuditInputs
from guarded_continuation import GUARD
from prepare_formatter_nested_fixture import second_immediate_extension
from prepare_formatter_report_signext_fixture import promote as promote_signext
from prepare_formatter_report_post_signext_immediate_fixture import (
    promote as promote_second, render as render_second,
)

SIBLING=0x80030000
NOOP=0x60000000


def extsb(reg=9):
    return ((31 << 26) | (reg << 21) |
            (reg << 16) | (954 << 1))


def addi(dst=11, imm=0xfffe):
    return ((14 << 26) | (dst << 21) | imm)


class NestedSecondImmediateTests(unittest.TestCase):
    def setUp(self):
        base=AuditInputs(
            'test_constant_written_by_121_is_symbolic_input_to_122')
        base.setUp()
        self.base=base
        self.immediate,self.copy,self.predecessor,self.compare=base.inputs(extsb())
        self.signext=promote_signext(
            self.immediate,self.copy,self.predecessor,self.compare,addi())
        self.second=promote_second(
            self.signext,self.immediate,self.copy,
            self.predecessor,self.compare,NOOP)
        self.old={**self.signext[0],SIBLING:(NOOP,GUARD)}

    def test_exact_guard_move_and_sibling_preservation(self):
        root=self.base.root
        merged,info=second_immediate_extension(
            self.old,self.signext,self.second)
        self.assertEqual(info,self.second[1])
        self.assertEqual(merged[root],(
            self.base.load,self.base.cmp,self.base.copy_word,
            self.base.imm,extsb(),addi(),NOOP,GUARD))
        self.assertEqual(merged[SIBLING],(NOOP,GUARD))
        self.assertEqual(self.old[root][-1],GUARD)
        self.assertEqual(self.signext[0][root][-1],GUARD)
        self.assertEqual(len(merged[root])*4,32)
        self.assertIn('formatter_report_second_immediate_private',
                      render_second(self.second))

    def test_predecessor_signext_may_have_independent_source(self):
        for reg, before, value in ((7,0x81234567,0x67),
                                    (9,0x5a,0x5a)):
            with self.subTest(reg=reg):
                immediate,copy,predecessor,compare=self.base.inputs(extsb(reg))
                original=promote_signext(
                    immediate,copy,predecessor,compare,addi(3,0x8000))
                second=promote_second(
                    original,immediate,copy,
                    predecessor,compare,NOOP)
                prior={**original[0],SIBLING:(NOOP,GUARD)}
                merged,info=second_immediate_extension(prior,original,second)
                self.assertEqual(original[1][5:8],(reg,before,value))
                self.assertEqual(info[5:7],(3,0xffff8000))
                self.assertEqual(merged[self.base.root][-3:],
                                 (addi(3,0x8000),NOOP,GUARD))

    def test_reject_modified_predecessor_and_sibling(self):
        root=self.base.root
        oldroot=self.old[root]
        mutations=(
            {**self.old,root:oldroot[:-2]+(NOOP,GUARD)},
            {**self.old,root:oldroot[:5]+(0,GUARD)},
            {**self.old,root+4:(0,GUARD)},
        )
        for before in mutations:
            with self.subTest(predecessor=tuple(before)):
                with self.assertRaises(ValueError):
                    second_immediate_extension(before,self.signext,self.second)
        tampered=(
            ({**self.second[0],root:self.second[0][root][:-1]+(0,)},
             self.second[1]),
            (self.second[0],self.second[1][:4]+(GUARD,)+self.second[1][5:]),
            (self.second[0],self.second[1][:-1]+(root+28,)),
            ({**self.second[0],SIBLING:(NOOP,GUARD)},self.second[1]),
        )
        for forged in tampered:
            with self.subTest(contract=forged[1]):
                with self.assertRaises(ValueError):
                    second_immediate_extension(self.old,self.signext,forged)

    def test_no_123_mode_without_122_predecessor(self):
        with self.assertRaises(ValueError):
            second_immediate_extension(self.old,self.immediate,self.second)

    def test_full_fixture_cli_scope_and_native_hooks_wired(self):
        source=Path(__file__).with_name(
            'prepare_formatter_nested_fixture.py').read_text()
        expected=(
            "modes.add_argument('--caller-report-second-immediate',action='store_true')",
            'if q.caller_report_second_immediate:q.caller_report_signext=True',
            'second_immediate_contract=report_second_immediate_plan(',
            'second_immediate_extension(expanded,signext_contract,second_immediate_contract)',
            'second_immediate_extension(final,signext_contract,second_immediate_contract)',
            'else 32 if second_immediate_contract is not None else 28',
            'render_report_second_immediate(second_immediate_contract)',
            'expected[ti[3]]=(ti[0],ti[4])',
            'second_immediate_contract=second_immediate_contract',
        )
        for fragment in expected:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment,source)
        self.assertEqual(source.count(
            "if second_immediate_contract is not None and signext_contract is None:"
            "raise ValueError('nested fixture mode')"),3)
        self.assertEqual(source.count(
            'signext_contract=signext_contract,second_immediate_contract=second_immediate_contract'),3)
        self.assertIn('nested fixture report second immediate predecessor',source)


if __name__=='__main__':
    unittest.main()
