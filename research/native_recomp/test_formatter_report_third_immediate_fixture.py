#!/usr/bin/env python3
"""Synthetic original-free provenance tests for guarded instruction 124."""
import unittest
from unittest.mock import patch

from audit_formatter_report_second_immediate_successor import Tests as AuditInputs
from guarded_continuation import GUARD
from prepare_formatter_report_third_immediate_fixture import (
    EXPECTED_COUNTS, plan, promote, render,
)

FOLLOWING = 0x60000000


class ThirdImmediateFixtureTests(unittest.TestCase):
    def setUp(self):
        self.base = AuditInputs(
            'test_second_immediate_constant_reaches_next_original_word')
        self.base.setUp()

    def contracts(self, word=None):
        if word is None:
            word = self.base.addi(6, 0, 0xff80)
        return self.base.inputs(next_word=word)

    def test_single_guard_advance_and_sign_extension(self):
        before = self.contracts()
        after = promote(*before, FOLLOWING)
        root = self.base.base.root
        self.assertEqual(len(before[0][0][root]), 8)
        self.assertEqual(len(after[0][root]), 9)
        self.assertEqual(after[0][root][:-2], before[0][0][root][:-1])
        self.assertEqual(after[0][root][-2:], (FOLLOWING, GUARD))
        self.assertEqual(after[1], (
            root, root+24, self.base.addi(6, 0, 0xff80),
            root+28, FOLLOWING, 6, 0xffffff80, root+0x100))
        self.assertEqual(EXPECTED_COUNTS, (0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0))
        rendered = render(after)
        self.assertIn('destination_reg=6u', rendered)
        self.assertIn('value=0xffffff80u', rendered)

    def test_every_immediate_edge_and_volatile_target(self):
        for imm, value in ((0, 0), (1, 1), (0x7fff, 0x7fff),
                           (0x8000, 0xffff8000), (0xffff, 0xffffffff)):
            for reg in (0, 3, 5, 12):
                with self.subTest(imm=imm, reg=reg):
                    result = promote(
                        *self.contracts(self.base.addi(reg, 0, imm)),
                        FOLLOWING)
                    self.assertEqual(result[1][5:7], (reg, value))
                    render(result)

    def test_rejects_nonzero_inputs_and_nonvolatile_targets(self):
        for word in (self.base.addi(6, 11, 1),
                     self.base.addi(6, 9, 0),
                     self.base.addi(1, 0, 1),
                     self.base.addi(2, 0, 1),
                     self.base.addi(13, 0, 1),
                     self.base.addi(31, 0, 1),
                     (15<<26)|(6<<21)|1,
                     0x60000000, GUARD):
            with self.subTest(word=word):
                with self.assertRaises(ValueError):
                    promote(*self.contracts(word), FOLLOWING)

    def test_rejects_guard_corruption_and_modified_predecessor(self):
        inputs = self.contracts()
        second, signext, immediate, copy, predecessor, compare = inputs
        root = self.base.base.root
        blocks, fields = second
        bad = (
            ({**blocks, root: blocks[root][:-1] + (0,)}, fields),
            (blocks, fields[:4] + (GUARD,) + fields[5:]),
            (blocks, fields[:5] + (0,) + fields[6:]),
            (blocks, fields[:-1] + (root+32,)),
        )
        for candidate in bad:
            with self.subTest(candidate=candidate[1]):
                with self.assertRaises(ValueError):
                    promote(candidate, signext, immediate, copy,
                            predecessor, compare, FOLLOWING)
        for word in (GUARD, -1, 0x100000000, True):
            with self.subTest(word=word):
                with self.assertRaises(ValueError):
                    promote(*inputs, word)

    def test_render_refuses_provenance_change_and_overlap(self):
        blocks, fields = promote(*self.contracts(), FOLLOWING)
        root = self.base.base.root
        original = blocks[root]
        mutations = (
            {},
            {**blocks, root: list(original)},
            {**blocks, root: original[:-1]},
            {**blocks, root: original[:6] + (original[6]^1,) + original[7:]},
            {**blocks, root: original[:7] + (0,) + original[8:]},
            {**blocks, root: original[:-1] + (0,)},
            {**blocks, root+4: (0x60000000, GUARD)},
        )
        for mutated in mutations:
            with self.subTest(paths=tuple(mutated)):
                with self.assertRaises(ValueError):
                    render((mutated, fields))
        for mutated in (
            fields[:6] + (0,) + fields[7:],
            fields[:3] + (root+32,) + fields[4:],
            fields[:-1] + (root+32,),
        ):
            with self.assertRaises(ValueError):
                render((blocks, mutated))

    def test_plan_carries_exact_8_owner_words_and_shared_state(self):
        inputs = self.contracts()
        second, signext, immediate, copy, predecessor, compare = inputs
        root = self.base.base.root
        actual = second[0][root][:7] + (FOLLOWING,)
        mocks = (
            patch('prepare_formatter_report_third_immediate_fixture.byte_plan',
                  return_value=predecessor),
            patch('prepare_formatter_report_third_immediate_fixture.compare_plan',
                  return_value=compare),
            patch('prepare_formatter_report_third_immediate_fixture.copy_plan',
                  return_value=copy),
            patch('prepare_formatter_report_third_immediate_fixture.immediate_plan',
                  return_value=immediate),
            patch('prepare_formatter_report_third_immediate_fixture.signext_plan',
                  return_value=signext),
            patch('prepare_formatter_report_third_immediate_fixture.second_immediate_plan',
                  return_value=second),
            patch('prepare_formatter_report_third_immediate_fixture.parse_functions',
                  return_value={root: 64}),
            patch('prepare_formatter_report_third_immediate_fixture.exact_words',
                  return_value=actual),
        )
        with mocks[0] as b, mocks[1] as c, mocks[2] as d, \
             mocks[3] as e, mocks[4] as f, mocks[5] as g, \
             mocks[6], mocks[7] as words:
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
        words.assert_called_once_with(b'fake dol', b'fake elf', root, 8)
        with patch('prepare_formatter_report_third_immediate_fixture.parse_functions',
                   return_value={root: 28}):
            with self.assertRaisesRegex(ValueError, 'third immediate extent'):
                plan(b'a', b'b', predecessor=predecessor, compare=compare,
                     copy=copy, immediate=immediate, signext=signext,
                     second=second)
        with patch('prepare_formatter_report_third_immediate_fixture.parse_functions',
                   return_value={root: 64}), \
             patch('prepare_formatter_report_third_immediate_fixture.exact_words',
                   return_value=actual[:6] + (0, FOLLOWING)):
            with self.assertRaisesRegex(ValueError, 'third immediate original'):
                plan(b'a', b'b', predecessor=predecessor, compare=compare,
                     copy=copy, immediate=immediate, signext=signext,
                     second=second)


if __name__ == '__main__':
    unittest.main()
