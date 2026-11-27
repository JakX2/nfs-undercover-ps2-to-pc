#!/usr/bin/env python3
"""Original-free regressions for privately guarded instruction 125."""
import unittest
from unittest.mock import patch

from audit_formatter_report_third_immediate_successor import Tests as AuditInputs
from guarded_continuation import GUARD
from prepare_formatter_report_fourth_immediate_fixture import (
    EXPECTED_COUNTS, plan, promote, render,
)

FOLLOWING = 0x60000000
SIBLING = 0x80030000


class FourthImmediateFixtureTests(unittest.TestCase):
    def setUp(self):
        self.base = AuditInputs('test_instruction_124_result_reaches_next_input')
        self.base.setUp()

    def contracts(self, word=None, source=9, third_word=None):
        if word is None:
            word = self.base.base.addi(5, 0, 0xff80)
        return self.base.inputs(next_word=word, source=source,
                                third_word=third_word)

    def test_exact_seventh_successor_guard_and_render(self):
        before = self.contracts()
        after = promote(*before, FOLLOWING)
        root = self.base.base.base.root
        self.assertEqual(len(before[0][0][root]), 9)
        self.assertEqual(len(after[0][root]), 10)
        self.assertEqual(after[0][root][:-2],
                         before[0][0][root][:-1])
        self.assertEqual(after[0][root][-2:], (FOLLOWING, GUARD))
        self.assertEqual(after[1], (
            root, root + 28, self.base.base.addi(5, 0, 0xff80),
            root + 32, FOLLOWING, 5, 0xffffff80, root + 0x100))
        self.assertEqual(EXPECTED_COUNTS, (0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0))
        owner = render(after)
        self.assertIn('formatter_report_fourth_immediate_private', owner)
        self.assertIn('destination_reg=5u', owner)
        self.assertIn('value=0xffffff80u', owner)

    def test_full_signed_immediate_extremes_and_volatile_targets(self):
        for imm, value in ((0, 0), (1, 1), (0x7fff, 0x7fff),
                           (0x8000, 0xffff8000), (0xffff, 0xffffffff)):
            for dst in (0, 3, 5, 12):
                with self.subTest(imm=imm, dst=dst):
                    w = self.base.base.addi(dst, 0, imm)
                    result = promote(*self.contracts(w), FOLLOWING)
                    self.assertEqual(result[1][5:7], (dst, value))
                    render(result)

    def test_predecessor_signext_inputs_remain_independent(self):
        for source in (3, 7, 9):
            for imm in (0x7f, 0x80, 0xff):
                with self.subTest(source=source, imm=imm):
                    self.base.base.base.imm = (
                        self.base.base.addi(3, 0, imm))
                    contract = promote(*self.contracts(source=source), FOLLOWING)
                    self.assertEqual(contract[1][6], 0xffffff80)
                    self.assertEqual(contract[0][self.base.base.base.root][-1],
                                     GUARD)

    def test_rejects_nonzero_base_nonvolatile_and_invalid_words(self):
        for word in (
            self.base.base.addi(5, 6, 1),
            self.base.base.addi(5, 9, 0),
            self.base.base.addi(1, 0, 1),
            self.base.base.addi(2, 0, 1),
            self.base.base.addi(13, 0, 1),
            self.base.base.addi(31, 0, 1),
            (15 << 26) | (5 << 21) | 1,
            0x60000000,
            GUARD,
        ):
            with self.subTest(word=word):
                with self.assertRaises(ValueError):
                    promote(*self.contracts(word), FOLLOWING)

    def test_refuses_following_guard_corruption(self):
        original = self.contracts()
        for word in (GUARD, -1, 0x1_0000_0000, True):
            with self.subTest(word=word):
                with self.assertRaises(ValueError):
                    promote(*original, word)

    def test_refuses_forged_predecessor_and_return_aliases(self):
        original = self.contracts()
        third, second, signext, immediate, copy, predecessor, compare = original
        blocks, fields = third
        root = self.base.base.base.root
        variants = (
            ({**blocks, root: blocks[root][:-1] + (0,)}, fields),
            (blocks, fields[:4] + (GUARD,) + fields[5:]),
            (blocks, fields[:5] + (0,) + fields[6:]),
            (blocks, fields[:-1] + (root + 36,)),
        )
        for alteration in variants:
            with self.subTest(fields=alteration[1]):
                with self.assertRaises(ValueError):
                    promote(alteration, second, signext, immediate,
                            copy, predecessor, compare, FOLLOWING)
        for reg in (7,):
            corrupt = list(self.base.base.base.regs)
            corrupt[reg] = ('reg', reg)
            with self.assertRaises(ValueError):
                promote(third, second, signext, immediate, copy,
                        (predecessor[0], tuple(corrupt), 0),
                        compare, FOLLOWING)

    def test_render_refuses_word_guard_root_and_sibling_mutations(self):
        valid = promote(*self.contracts(), FOLLOWING)
        blocks, fields = valid
        root = self.base.base.base.root
        original = blocks[root]
        mutations = (
            {},
            {**blocks, root: list(original)},
            {**blocks, root: original[:-1]},
            {**blocks, root: original[:-1] + (0,)},
            {**blocks, root: original[:7] + (original[7]^1,) + original[8:]},
            {**blocks, root: original[:8] + (0,) + original[9:]},
            {**blocks, root+4: (0x60000000, GUARD)},
        )
        for changed in mutations:
            with self.subTest(roots=tuple(changed)):
                with self.assertRaises(ValueError):
                    render((changed, fields))
        for changed_fields in (
            fields[:6] + (0,) + fields[7:],
            fields[:3] + (root+36,) + fields[4:],
            fields[:-1] + (root+36,),
        ):
            with self.assertRaises(ValueError):
                render((blocks, changed_fields))
        # Unrelated siblings remain unchanged and outside this callee proof.
        third, second, signext, immediate, copy, pred, cmp = self.contracts()
        third = ({**third[0], SIBLING: (0x60000000, GUARD)}, third[1])
        # Do not claim a new sibling as authenticated by old fixture.
        with self.assertRaises(ValueError):
            promote(third, second, signext, immediate, copy,
                    pred, cmp, FOLLOWING)

    def test_plan_reuses_shared_predecessor_and_authentic_nine_words(self):
        third, second, signext, immediate, copy, predecessor, compare = (
            self.contracts())
        root = self.base.base.base.root
        actual = third[0][root][:8] + (FOLLOWING,)
        mocks = (
            patch('prepare_formatter_report_fourth_immediate_fixture.byte_plan',
                  return_value=predecessor),
            patch('prepare_formatter_report_fourth_immediate_fixture.compare_plan',
                  return_value=compare),
            patch('prepare_formatter_report_fourth_immediate_fixture.copy_plan',
                  return_value=copy),
            patch('prepare_formatter_report_fourth_immediate_fixture.immediate_plan',
                  return_value=immediate),
            patch('prepare_formatter_report_fourth_immediate_fixture.signext_plan',
                  return_value=signext),
            patch('prepare_formatter_report_fourth_immediate_fixture.second_immediate_plan',
                  return_value=second),
            patch('prepare_formatter_report_fourth_immediate_fixture.third_immediate_plan',
                  return_value=third),
            patch('prepare_formatter_report_fourth_immediate_fixture.parse_functions',
                  return_value={root: 64}),
            patch('prepare_formatter_report_fourth_immediate_fixture.exact_words',
                  return_value=actual),
        )
        with mocks[0] as b, mocks[1] as c, mocks[2] as d, \
             mocks[3] as e, mocks[4] as f, mocks[5] as g, \
             mocks[6] as h, mocks[7], mocks[8] as words:
            result = plan(b'fake dol', b'fake elf')
        self.assertEqual(result[1][6], 0xffffff80)
        b.assert_called_once_with(b'fake dol', b'fake elf', with_live=True)
        c.assert_called_once_with(b'fake dol', b'fake elf',
                                  predecessor=predecessor)
        d.assert_called_once_with(b'fake dol', b'fake elf',
                                  predecessor=predecessor, compare=compare)
        e.assert_called_once_with(b'fake dol', b'fake elf',
                                  predecessor=predecessor, compare=compare,
                                  copy=copy)
        f.assert_called_once_with(b'fake dol', b'fake elf',
                                  predecessor=predecessor, compare=compare,
                                  copy=copy, immediate=immediate)
        g.assert_called_once_with(b'fake dol', b'fake elf',
                                  predecessor=predecessor, compare=compare,
                                  copy=copy, immediate=immediate, signext=signext)
        h.assert_called_once_with(b'fake dol', b'fake elf',
                                  predecessor=predecessor, compare=compare,
                                  copy=copy, immediate=immediate, signext=signext,
                                  second=second)
        words.assert_called_once_with(b'fake dol', b'fake elf', root, 9)
        with patch('prepare_formatter_report_fourth_immediate_fixture.parse_functions',
                   return_value={root: 32}):
            with self.assertRaisesRegex(ValueError,'fourth immediate extent'):
                plan(b'a',b'b',predecessor=predecessor,compare=compare,copy=copy,
                     immediate=immediate,signext=signext,second=second,third=third)
        with patch('prepare_formatter_report_fourth_immediate_fixture.parse_functions',
                   return_value={root: 64}), \
             patch('prepare_formatter_report_fourth_immediate_fixture.exact_words',
                   return_value=actual[:7] + (0, FOLLOWING)):
            with self.assertRaisesRegex(ValueError,'fourth immediate original'):
                plan(b'a',b'b',predecessor=predecessor,compare=compare,copy=copy,
                     immediate=immediate,signext=signext,second=second,third=third)


if __name__ == '__main__':
    unittest.main()
