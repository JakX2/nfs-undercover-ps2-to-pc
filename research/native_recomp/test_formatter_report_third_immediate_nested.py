#!/usr/bin/env python3
"""Original-free regressions for nested original 124 immediate installation."""
import unittest
from pathlib import Path

from audit_formatter_report_second_immediate_successor import Tests as AuditInputs
from guarded_continuation import GUARD
from prepare_formatter_nested_fixture import third_immediate_extension
from prepare_formatter_report_third_immediate_fixture import (
    promote as promote_third, render as render_third,
)

SIBLING=0x80030000
NOOP=0x60000000


class NestedThirdImmediateTests(unittest.TestCase):
    def setUp(self):
        self.audit=AuditInputs(
            'test_second_immediate_constant_reaches_next_original_word')
        self.audit.setUp()
        self.second,self.signext,self.immediate,self.copy,self.predecessor,self.compare=(
            self.audit.inputs(next_word=self.audit.addi(6,0,0xff80)))
        self.third=promote_third(
            self.second,self.signext,self.immediate,self.copy,
            self.predecessor,self.compare,NOOP)
        self.old={**self.second[0],SIBLING:(NOOP,GUARD)}

    def test_exact_guard_move_and_sibling_preservation(self):
        root=self.audit.base.root
        merged,info=third_immediate_extension(
            self.old,self.second,self.third)
        self.assertEqual(info,self.third[1])
        self.assertEqual(len(merged[root])*4,36)
        self.assertEqual(merged[root],(
            self.audit.base.load,self.audit.base.cmp,self.audit.base.copy_word,
            self.audit.base.imm,self.signext[1][2],self.second[1][2],
            self.third[1][2],NOOP,GUARD))
        self.assertEqual(merged[SIBLING],(NOOP,GUARD))
        self.assertEqual(self.old[root][-1],GUARD)
        self.assertEqual(self.second[0][root][-1],GUARD)
        self.assertEqual(info[5:7],(6,0xffffff80))
        self.assertIn('formatter_report_third_immediate_private',
                      render_third(self.third))

    def test_predecessor_signext_independent_and_124_zero_base(self):
        for source in (3,7,9):
            for imm,value in ((0,0),(0x7fff,0x7fff),
                              (0x8000,0xffff8000),(0xffff,0xffffffff)):
                with self.subTest(source=source,imm=imm):
                    second,signext,immediate,copy,predecessor,compare=(
                        self.audit.inputs(
                            next_word=self.audit.addi(5,0,imm),
                            source=source))
                    third=promote_third(
                        second,signext,immediate,copy,
                        predecessor,compare,NOOP)
                    prior={**second[0],SIBLING:(NOOP,GUARD)}
                    merged,info=third_immediate_extension(prior,second,third)
                    self.assertEqual(info[5:7],(5,value))
                    self.assertEqual(merged[self.audit.base.root][-3:],
                                     (self.audit.addi(5,0,imm),NOOP,GUARD))
                    self.assertEqual(merged[SIBLING],(NOOP,GUARD))

    def test_refuse_mutated_prior_word_guard_and_siblings(self):
        root=self.audit.base.root
        oldroot=self.old[root]
        mutations=(
            {**self.old,root:oldroot[:-1]+(0,)},
            {**self.old,root:oldroot[:5]+(0,)+oldroot[6:]},
            {**self.old,root+4:(0,GUARD)},
            {**self.old,SIBLING:(0,GUARD)},
        )
        for before in mutations:
            with self.subTest(before=tuple(before)):
                with self.assertRaises(ValueError):
                    third_immediate_extension(before,self.second,self.third)
        blocks,fields=self.third
        altered=(
            ({**blocks,root:blocks[root][:-1]+(0,)},fields),
            (blocks,fields[:4]+(GUARD,)+fields[5:]),
            (blocks,fields[:5]+(0,)+fields[6:]),
            (blocks,fields[:-1]+(root+32,)),
            ({**blocks,SIBLING:(NOOP,GUARD)},fields),
        )
        for candidate in altered:
            with self.subTest(candidate=candidate[1]):
                with self.assertRaises(ValueError):
                    third_immediate_extension(self.old,self.second,candidate)

    def test_no_124_without_123_predecessor_or_overlap(self):
        with self.assertRaises(ValueError):
            third_immediate_extension(self.old,self.signext,self.third)
        with self.assertRaises(ValueError):
            third_immediate_extension(self.old,None,self.third)
        with self.assertRaises(ValueError):
            third_immediate_extension(self.old,self.second,None)
        forged={**self.old,self.audit.base.root+4:(NOOP,GUARD)}
        with self.assertRaises(ValueError):
            third_immediate_extension(forged,self.second,self.third)

    def test_fixture_scope_and_install_are_all_wired(self):
        source=Path(__file__).with_name(
            'prepare_formatter_nested_fixture.py').read_text()
        expected=(
            "modes.add_argument('--caller-report-third-immediate',action='store_true')",
            'if q.caller_report_third_immediate:q.caller_report_second_immediate=True',
            'third_immediate_contract=report_third_immediate_plan(',
            'third_immediate_extension(expanded,second_immediate_contract,third_immediate_contract)',
            'third_immediate_extension(final,second_immediate_contract,third_immediate_contract)',
            'extent=36 if third_immediate_contract is not None else 32',
            'render_report_third_immediate(third_immediate_contract)',
            'expected[ui[3]]=(ui[0],ui[4])',
            'third_immediate_contract=third_immediate_contract',
        )
        for fragment in expected:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment,source)
        self.assertEqual(source.count(
            "if third_immediate_contract is not None and second_immediate_contract is None:"
            "raise ValueError('nested fixture mode')"),3)
        self.assertEqual(source.count(
            'second_immediate_contract=second_immediate_contract,third_immediate_contract=third_immediate_contract'),3)
        self.assertIn('nested fixture report third immediate predecessor',source)


if __name__=='__main__':
    unittest.main()
