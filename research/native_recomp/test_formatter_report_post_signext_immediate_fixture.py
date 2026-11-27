#!/usr/bin/env python3
"""Original-free regressions for private instruction-123 immediate fixture."""
import unittest
from unittest.mock import patch

from audit_formatter_report_immediate_successor import Tests as AuditInputs
from guarded_continuation import GUARD
from prepare_formatter_report_signext_fixture import promote as promote_signext
from prepare_formatter_report_post_signext_immediate_fixture import (
    EXPECTED_COUNTS, plan, promote, render, zero_immediate,
)

FOLLOWING = 0x60000000


def extsb(reg=9):
    return ((31 << 26) | (reg << 21) |
            (reg << 16) | (954 << 1))


def addi(dst=11, imm=0xfffe, base=0, op=14):
    return ((op << 26) | (dst << 21) |
            (base << 16) | (imm & 0xffff))


class SecondImmediateFixtureTests(unittest.TestCase):
    def setUp(self):
        self.base = AuditInputs(
            'test_constant_written_by_121_is_symbolic_input_to_122')
        self.base.setUp()

    def contracts(self, second=None, source=9):
        immediate, copy, predecessor, compare = self.base.inputs(extsb(source))
        signext = promote_signext(immediate, copy, predecessor,
                                 compare, addi() if second is None else second)
        return signext, immediate, copy, predecessor, compare

    def test_exact_sixth_instruction_guard_move(self):
        signext, immediate, copy, predecessor, compare = self.contracts()
        contract = promote(signext, immediate, copy, predecessor,
                           compare, FOLLOWING)
        root = self.base.root
        self.assertEqual(contract[0][root],
                         (self.base.load, self.base.cmp, self.base.copy_word,
                          self.base.imm, extsb(), addi(), FOLLOWING, GUARD))
        self.assertEqual(contract[1], (root, root+20, addi(),
                                        root+24, FOLLOWING, 11,
                                        0xfffffffe, root+0x100))
        self.assertEqual(signext[0][root][-1], GUARD)
        self.assertEqual(EXPECTED_COUNTS,
                         (0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0))
        owner_header = render(contract)
        self.assertIn('destination_reg=11u', owner_header)
        self.assertIn('value=0xfffffffeu', owner_header)
        self.assertIn('next_pc=', owner_header)

    def test_signed_extremes_volatile_destinations(self):
        for imm, value in ((0, 0), (1, 1), (0x7fff, 0x7fff),
                           (0x8000, 0xffff8000), (0xffff, 0xffffffff)):
            for dst in (0, 3, 10, 12):
                with self.subTest(imm=imm, dst=dst):
                    w = addi(dst=dst, imm=imm)
                    contract = promote(*self.contracts(w), FOLLOWING)
                    self.assertEqual(contract[1][5:7], (dst, value))
                    render(contract)
                    self.assertEqual(zero_immediate(w), (dst, value))

    def test_all_256_signext_inputs_do_not_affect_zero_base_123(self):
        for low in range(256):
            with self.subTest(low=low):
                self.base.imm = addi(dst=3, imm=low)
                contract = promote(*self.contracts(addi(dst=3, imm=0xff80),
                                                     source=3), FOLLOWING)
                self.assertEqual(contract[1][5:7], (3, 0xffff_ff80))
        for source in (7, 9):
            contract = promote(*self.contracts(source=source), FOLLOWING)
            self.assertEqual(contract[1][5:7], (11, 0xfffffffe))

    def test_unknown_or_nonvolatile_and_mutated_123_refused(self):
        for word in (addi(dst=1), addi(dst=2), addi(dst=13),
                     addi(dst=14), addi(dst=31), addi(base=7),
                     addi(op=15), extsb(9), GUARD, -1, True):
            with self.subTest(word=word):
                with self.assertRaises(ValueError):
                    promote(*self.contracts(word), FOLLOWING)
        for word in (addi(dst=1), addi(dst=13), addi(base=9), addi(op=15)):
            with self.assertRaisesRegex(ValueError, 'second immediate encoding'):
                zero_immediate(word)

    def test_following_guard_must_not_be_reused(self):
        for word in (GUARD, -1, 0x1_0000_0000, True):
            with self.subTest(word=word):
                with self.assertRaises(ValueError):
                    promote(*self.contracts(), word)

    def test_predecessor_and_full_guard_cannot_be_forged(self):
        signext, immediate, copy, predecessor, compare = self.contracts()
        root = self.base.root
        blocks, fields = signext
        forged = (
            ({**blocks, root: blocks[root][:-1] + (0,)}, fields),
            (blocks, fields[:4] + (0,) + fields[5:]),
            (blocks, fields[:6] + (0,) + fields[7:]),
            (blocks, fields[:-1] + (root+28,)),
        )
        for alteration in forged:
            with self.subTest(alteration=alteration[1]):
                with self.assertRaises(ValueError):
                    promote(alteration, immediate, copy, predecessor,
                            compare, FOLLOWING)
        valid = promote(signext, immediate, copy, predecessor,
                        compare, FOLLOWING)
        original = valid[0][root]
        for modified in ({},
                         {**valid[0], root: original[:-1]},
                         {**valid[0], root: original[:-1] + (0,)},
                         {**valid[0], root: original[:5] + (addi() ^ 1,) +
                          original[6:]},
                         {**valid[0], root: original[:6] + (0,) + original[7:]},
                         {**valid[0], root+4: (0x60000000, GUARD)}):
            with self.assertRaisesRegex(ValueError,
                                        'report second immediate rendering'):
                render((modified, valid[1]))

    def test_plan_reuses_shared_authenticated_state(self):
        signext, immediate, copy, predecessor, compare = self.contracts()
        root = self.base.root
        original = signext[0][root][:6] + (FOLLOWING,)
        mocks = (
            patch('prepare_formatter_report_post_signext_immediate_fixture.byte_plan',
                  return_value=predecessor),
            patch('prepare_formatter_report_post_signext_immediate_fixture.compare_plan',
                  return_value=compare),
            patch('prepare_formatter_report_post_signext_immediate_fixture.copy_plan',
                  return_value=copy),
            patch('prepare_formatter_report_post_signext_immediate_fixture.immediate_plan',
                  return_value=immediate),
            patch('prepare_formatter_report_post_signext_immediate_fixture.signext_plan',
                  return_value=signext),
            patch('prepare_formatter_report_post_signext_immediate_fixture.parse_functions',
                  return_value={root: 64}),
            patch('prepare_formatter_report_post_signext_immediate_fixture.exact_words',
                  return_value=original),
        )
        with mocks[0] as b, mocks[1] as c, mocks[2] as d, \
             mocks[3] as e, mocks[4] as f, mocks[5], mocks[6] as words:
            result = plan(b'fake dol', b'fake elf')
        self.assertEqual(result[1][6], 0xfffffffe)
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
        words.assert_called_once_with(b'fake dol', b'fake elf', root, 7)
        with patch('prepare_formatter_report_post_signext_immediate_fixture.parse_functions',
                   return_value={root: 24}):
            with self.assertRaisesRegex(ValueError, 'second immediate extent'):
                plan(b'a', b'b', predecessor=predecessor, compare=compare,
                     copy=copy, immediate=immediate, signext=signext)
        with patch('prepare_formatter_report_post_signext_immediate_fixture.parse_functions',
                   return_value={root: 64}), \
             patch('prepare_formatter_report_post_signext_immediate_fixture.exact_words',
                   return_value=original[:5] + (0, FOLLOWING)):
            with self.assertRaisesRegex(ValueError, 'second immediate original'):
                plan(b'a', b'b', predecessor=predecessor, compare=compare,
                     copy=copy, immediate=immediate, signext=signext)


if __name__ == '__main__':
    unittest.main()
