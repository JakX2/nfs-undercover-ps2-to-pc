#!/usr/bin/env python3
"""Synthetic-only regressions for original 122 extsb fixture admission."""
import unittest
from unittest.mock import patch

from audit_formatter_report_immediate_successor import Tests as AuditInputs
from guarded_continuation import GUARD
from prepare_formatter_report_signext_fixture import (
    EXPECTED_COUNTS, encoding, plan, promote, render, sign_extend_byte,
)

FOLLOWING = 0x60000000


def extsb(reg=3, dst=None, rc=0, rb=0, xo=954):
    if dst is None:
        dst = reg
    return ((31 << 26) | (reg << 21) | (dst << 16) |
            (rb << 11) | (xo << 1) | rc)


class SignextFixtureTests(unittest.TestCase):
    def setUp(self):
        self.base = AuditInputs('test_constant_written_by_121_is_symbolic_input_to_122')
        self.base.setUp()

    def contracts(self, word=None):
        return self.base.inputs(extsb() if word is None else word)

    def test_exact_fifth_slot_and_private_render(self):
        immediate, copy, predecessor, compare = self.contracts()
        contract = promote(immediate, copy, predecessor, compare, FOLLOWING)
        root = self.base.root
        self.assertEqual(contract[0][root],
                         (self.base.load, self.base.cmp,
                          self.base.copy_word, self.base.imm,
                          extsb(), FOLLOWING, GUARD))
        self.assertEqual(contract[1],
                         (root, root+16, extsb(), root+20,
                          FOLLOWING, 3, 0xfffffffe, 0xfffffffe,
                          root+0x100))
        self.assertEqual(immediate[0][root][-1], GUARD)
        self.assertEqual(EXPECTED_COUNTS, (1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1))
        private = render(contract)
        self.assertIn('destination_reg=3u', private)
        self.assertIn('output_value=0xfffffffeu', private)
        self.assertIn('next_pc=', private)

    def test_all_256_byte_values_and_sign_boundaries(self):
        for byte in range(256):
            with self.subTest(byte=byte):
                self.base.imm = (14 << 26) | (3 << 21) | byte
                inputs = self.contracts()
                result = promote(*inputs, FOLLOWING)
                expected = byte if byte < 128 else 0xffffff00 | byte
                self.assertEqual(result[1][7], expected)
                self.assertEqual(sign_extend_byte(result[1][6]), expected)
                render(result)
        for imm, value in ((0x7fff, 0xffffffff), (0x8000, 0),
                           (0xff80, 0xffffff80), (0xffff, 0xffffffff)):
            self.base.imm = (14 << 26) | (3 << 21) | imm
            self.assertEqual(promote(*self.contracts(), FOLLOWING)[1][7],
                             value)

    def test_decoder_denies_record_nonalias_and_unmodeled(self):
        bad = (extsb(dst=4), extsb(rc=1), extsb(rb=1),
               extsb(xo=922), extsb(xo=955), 0x60000000,
               extsb(reg=1), extsb(reg=13), GUARD, -1, True)
        for word in bad:
            with self.subTest(word=word):
                with self.assertRaises(ValueError):
                    promote(*self.contracts(word), FOLLOWING)
        for word in (extsb(dst=4), extsb(rc=1), extsb(rb=1),
                     extsb(xo=922), extsb(xo=955)):
            with self.assertRaisesRegex(ValueError, 'report signext encoding'):
                encoding(word)
        self.assertEqual(encoding(extsb()), 3)
        for value in (True, -1, 0x100000000):
            with self.assertRaises(ValueError):
                sign_extend_byte(value)

    def test_authenticated_source_can_precede_immediate(self):
        # Original 122 must not be assumed to consume the result of 121.
        # Earlier byte loads and seeded constants can also be proven inputs.
        for reg, before, expected in ((9, 0x5a, 0x5a),
                                      (7, 0x81234567, 0x67)):
            with self.subTest(reg=reg):
                contract = promote(*self.contracts(extsb(reg)), FOLLOWING)
                self.assertEqual(contract[1][5:8], (reg, before, expected))
                render(contract)
        with self.assertRaisesRegex(ValueError, 'signext provenance'):
            promote(*self.contracts(extsb(8)), FOLLOWING)

    def test_zero_and_other_volatile_registers(self):
        for reg in (0, 3, 4, 9, 12):
            with self.subTest(reg=reg):
                self.base.imm = (14 << 26) | (reg << 21) | 0x80
                result = promote(*self.contracts(extsb(reg)), FOLLOWING)
                self.assertEqual(result[1][5:8],
                                 (reg, 0x80, 0xffffff80))

    def test_following_guard_not_consumed_as_instruction(self):
        for word in (GUARD, -1, 0x100000000, False):
            with self.subTest(word=word):
                with self.assertRaises(ValueError):
                    promote(*self.contracts(), word)

    def test_authenticated_predecessor_cannot_be_forged(self):
        immediate, copy, predecessor, compare = self.contracts()
        blocks, fields = immediate
        forged = (
            ({**blocks, self.base.root: blocks[self.base.root][:-1] + (0,)}, fields),
            (blocks, fields[:6] + (0,) + fields[7:]),
            (blocks, fields[:5] + (4,) + fields[6:]),
            (blocks, fields[:-1] + (self.base.root+24,)),
        )
        for alteration in forged:
            with self.subTest(alteration=alteration[1]):
                with self.assertRaises(ValueError):
                    promote(alteration, copy, predecessor, compare, FOLLOWING)
        bad_reg = list(self.base.regs)
        bad_reg[7] = ('reg', 7)
        with self.assertRaises(ValueError):
            promote(immediate, copy,
                    (predecessor[0], tuple(bad_reg), 0), compare, FOLLOWING)
        good = promote(immediate, copy, predecessor, compare, FOLLOWING)
        fields = good[1]
        for modified in (fields[:7] + (0,) + fields[8:],
                         fields[:3] + (self.base.root+24,) + fields[4:],
                         fields[:5] + (4,) + fields[6:]):
            with self.assertRaises(ValueError):
                render((good[0], modified))

    def test_owner_word_match_extent_and_shared_predecessor(self):
        immediate, copy, predecessor, compare = self.contracts()
        root = self.base.root
        original = immediate[0][root][:5] + (FOLLOWING,)
        mocks = (
            patch('prepare_formatter_report_signext_fixture.byte_plan',
                  return_value=predecessor),
            patch('prepare_formatter_report_signext_fixture.compare_plan',
                  return_value=compare),
            patch('prepare_formatter_report_signext_fixture.copy_plan',
                  return_value=copy),
            patch('prepare_formatter_report_signext_fixture.immediate_plan',
                  return_value=immediate),
            patch('prepare_formatter_report_signext_fixture.parse_functions',
                  return_value={root: 64}),
            patch('prepare_formatter_report_signext_fixture.exact_words',
                  return_value=original),
        )
        with mocks[0] as b, mocks[1] as c, mocks[2] as d, \
             mocks[3] as e, mocks[4], mocks[5] as words:
            result = plan(b'fake dol', b'fake elf')
        self.assertEqual(result[1][7], 0xfffffffe)
        b.assert_called_once_with(b'fake dol', b'fake elf', with_live=True)
        c.assert_called_once_with(b'fake dol', b'fake elf',
                                  predecessor=predecessor)
        d.assert_called_once_with(b'fake dol', b'fake elf',
                                  predecessor=predecessor, compare=compare)
        e.assert_called_once_with(b'fake dol', b'fake elf',
                                  predecessor=predecessor, compare=compare,
                                  copy=copy)
        words.assert_called_once_with(b'fake dol', b'fake elf', root, 6)
        with patch('prepare_formatter_report_signext_fixture.parse_functions',
                   return_value={root: 20}):
            with self.assertRaisesRegex(ValueError, 'report signext extent'):
                plan(b'a', b'b', predecessor=predecessor, compare=compare,
                     copy=copy, immediate=immediate)
        with patch('prepare_formatter_report_signext_fixture.parse_functions',
                   return_value={root: 64}), \
             patch('prepare_formatter_report_signext_fixture.exact_words',
                   return_value=original[:4] + (0, FOLLOWING)):
            with self.assertRaisesRegex(ValueError, 'report signext original'):
                plan(b'a', b'b', predecessor=predecessor, compare=compare,
                     copy=copy, immediate=immediate)


if __name__ == '__main__':
    unittest.main()
