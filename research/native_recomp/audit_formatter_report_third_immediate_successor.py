#!/usr/bin/env python3
"""Read-only, fail-closed provenance of original formatter instruction 125.

Reconstruct the original 118 byte load, 119 compare, 120 stack move,
121 zero-input addi, 122 extsb, 123 zero-input addi and 124 zero-input
addi from one authenticated live-register snapshot. Classify the 125th
original word without compiling, interpreting, or executing that word.
Original words, guest PCs, operands and values remain owner-private.
"""
import argparse
import struct
import unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch

from audit_formatter_partial_copy import boundary_shape
from audit_formatter_partial_integer import classify
from audit_formatter_report_second_immediate_successor import Tests as AuditInputs
from guarded_continuation import GUARD
from prepare_formatter_caller_integer_contract import step
from prepare_formatter_next_entry_report_byte_contract import plan as byte_plan
from prepare_formatter_report_compare_fixture import plan as compare_plan
from prepare_formatter_report_stack_copy_fixture import plan as copy_plan
from prepare_formatter_report_immediate_fixture import plan as immediate_plan
from prepare_formatter_report_signext_fixture import (
    plan as signext_plan, promote as promote_signext,
)
from prepare_formatter_report_post_signext_immediate_fixture import (
    plan as second_immediate_plan, promote as promote_second,
)
from prepare_formatter_report_third_immediate_fixture import (
    plan as third_immediate_plan, promote as promote_third,
)
from prepare_v419_full_start import MAX_DOL
from private_plan_cache import plan_cache_scope

_ALLOWED = frozenset({
    'caller integer opcode', 'caller integer encoding',
    'caller integer effects', 'caller integer inputs',
    'caller integer registers',
})


def inspect(third, second, signext, immediate, copy, predecessor, compare):
    """Authenticate all seven original instructions before classifying 125."""
    if (not isinstance(third, tuple) or len(third) != 2 or
            not isinstance(third[1], tuple) or len(third[1]) != 8 or
            not isinstance(predecessor, tuple) or len(predecessor) != 3):
        raise ValueError('next third immediate contract')
    root, pc, word, next_pc, next_word, dst, value, ret = third[1]
    if (type(next_word) is not int or
            not 0 <= next_word <= 0xffffffff or next_word == GUARD):
        raise ValueError('next third immediate contract')
    try:
        expected = promote_third(
            second, signext, immediate, copy, predecessor, compare, next_word)
        if (third != expected or pc != root + 24 or
                next_pc != root + 28 or ret != second[1][7]):
            raise ValueError('contract mismatch')
    except (ValueError, KeyError, TypeError, IndexError) as error:
        raise ValueError('next third immediate provenance') from error

    byte, regs, saved = predecessor
    if (not isinstance(regs, (tuple, list)) or len(regs) != 32 or
            type(saved) is not int or not 0 <= saved <= 0xffffffff):
        raise ValueError('next third immediate state')
    try:
        after_load = list(regs)
        load, byte_value = byte[1][1], byte[1][4]
        after_load[(load >> 21) & 31] = ('const', byte_value)
        after_compare, _ = step(
            byte[1][6], tuple(after_load), saved_mask=saved)
        after_copy, copy_inputs = step(
            copy[1][2], after_compare,
            saved_mask=saved, allow_stack_copy=True)
        after_121, first_inputs = step(
            immediate[1][2], after_copy, saved_mask=saved)
        after_122, signed_inputs = step(
            signext[1][2], after_121, saved_mask=saved)
        after_123, second_inputs = step(
            second[1][2], after_122, saved_mask=saved)
        after_124, third_inputs = step(
            word, after_123, saved_mask=saved)
        if (copy_inputs or first_inputs or second_inputs or third_inputs or
                signed_inputs != ((signext[1][5], signext[1][6]),) or
                after_122[signext[1][5]] != ('const', signext[1][7]) or
                after_123[second[1][5]] != ('const', second[1][6]) or
                after_124[dst] != ('const', value) or
                after_124[1][0] != 'stack' or len(after_124) != 32):
            raise ValueError('state mismatch')
    except (ValueError, TypeError, IndexError, KeyError) as error:
        raise ValueError('next third immediate state') from error

    family = boundary_shape(next_word)
    if family != 'integer':
        return family, 'not_integer', (0,) * 11, 0, 'not_attempted'
    name, reads, writes, cr, carry, xer, oe = classify(next_word)
    read_set, write_set = set(reads), set(writes)
    kinds = Counter(after_124[i][0] for i in read_set)
    counts = (
        len(read_set), len(write_set), kinds['const'], kinds['stack'],
        kinds['partial'], len(read_set) -
        kinds['const'] - kinds['stack'] - kinds['partial'],
        cr, carry, xer, oe, int(bool(read_set & write_set)),
    )
    try:
        modeled, _ = step(
            next_word, after_124, saved_mask=saved,
            allow_stack_copy=True, allow_stack_relative=True)
        if len(modeled) != 32:
            raise ValueError('caller integer registers')
        reason = 'supported'
    except ValueError as error:
        modeled = None
        reason = (str(error) if str(error) in _ALLOWED
                  else 'not_modelled')
    return family, name, counts, int(modeled is not None), reason


def plan(dol, elf):
    predecessor = byte_plan(dol, elf, with_live=True)
    compare = compare_plan(dol, elf, predecessor=predecessor)
    copy = copy_plan(dol, elf, predecessor=predecessor, compare=compare)
    immediate = immediate_plan(
        dol, elf, predecessor=predecessor, compare=compare, copy=copy)
    signext = signext_plan(
        dol, elf, predecessor=predecessor, compare=compare,
        copy=copy, immediate=immediate)
    second = second_immediate_plan(
        dol, elf, predecessor=predecessor, compare=compare, copy=copy,
        immediate=immediate, signext=signext)
    third = third_immediate_plan(
        dol, elf, predecessor=predecessor, compare=compare, copy=copy,
        immediate=immediate, signext=signext, second=second)
    return inspect(third, second, signext, immediate, copy,
                   predecessor, compare)


class Tests(unittest.TestCase):
    def setUp(self):
        self.base = AuditInputs(
            'test_second_immediate_constant_reaches_next_original_word')
        self.base.setUp()
        self.third_word = self.base.addi(6, 0, 0xff80)

    def inputs(self, next_word=None, source=9, third_word=None):
        second, signext, immediate, copy, predecessor, compare = (
            self.base.inputs(
                next_word=self.third_word if third_word is None else third_word,
                source=source))
        next_word = (self.base.addi(5, 6, 1) if next_word is None
                     else next_word)
        third = promote_third(
            second, signext, immediate, copy, predecessor, compare,
            next_word)
        return third, second, signext, immediate, copy, predecessor, compare

    def test_instruction_124_result_reaches_next_input(self):
        result = inspect(*self.inputs())
        self.assertEqual((result[0], result[1], result[3:]),
                         ('integer', 'add_immediate', (1, 'supported')))
        self.assertEqual(result[2], (1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0))

    def test_alias_reads_124_result_and_preserves_other_registers(self):
        for source in (3, 7, 9):
            with self.subTest(source=source):
                result = inspect(*self.inputs(
                    self.base.addi(6, 6, 1), source=source))
                self.assertEqual(result[2], (1, 1, 1, 0, 0, 0,
                                              0, 0, 0, 0, 1))
                self.assertEqual(result[3:], (1, 'supported'))

    def test_zero_input_and_unknown_input_are_distinct(self):
        result = inspect(*self.inputs(self.base.addi(5, 0, 1)))
        self.assertEqual(result[2][0], 0)
        self.assertEqual(result[3:], (1, 'supported'))
        other = inspect(*self.inputs(self.base.addi(5, 8, 1)))
        self.assertEqual((other[2][5], other[3], other[4]),
                         (1, 0, 'caller integer inputs'))

    def test_non_integer_is_classified_never_executed(self):
        branch = (16 << 26) | (12 << 21) | (2 << 16) | 16
        self.assertEqual(inspect(*self.inputs(branch)),
                         ('branch', 'not_integer', (0,) * 11, 0,
                          'not_attempted'))

    def test_all_sign_extended_byte_inputs_still_valid(self):
        for byte in range(256):
            with self.subTest(byte=byte):
                self.base.base.imm = self.base.addi(3, 0, byte)
                result = inspect(*self.inputs(source=3))
                self.assertEqual(result[2][2:6], (1, 0, 0, 0))
                self.assertEqual(result[3:], (1, 'supported'))

    def test_corrupted_predecessor_and_return_guards_rejected(self):
        full = self.inputs()
        third, second, signext, immediate, copy, predecessor, compare = full
        blocks, fields = third
        root = self.base.base.root
        altered = (
            ({**blocks, root: blocks[root][:-1] + (0,)}, fields),
            (blocks, fields[:4] + (GUARD,) + fields[5:]),
            (blocks, fields[:6] + (0,) + fields[7:]),
            (blocks, fields[:-1] + (root + 32,)),
        )
        for candidate in altered:
            with self.subTest(candidate=candidate[1]):
                with self.assertRaises(ValueError):
                    inspect(candidate, second, signext, immediate, copy,
                            predecessor, compare)
        bad_reg = list(self.base.base.regs)
        bad_reg[7] = ('reg', 7)
        with self.assertRaises(ValueError):
            inspect(third, second, signext, immediate, copy,
                    (predecessor[0], tuple(bad_reg), 0), compare)

    def test_plan_reuses_authentication_chain(self):
        third, second, signext, immediate, copy, predecessor, compare = (
            self.inputs())
        with patch(__name__ + '.byte_plan', return_value=predecessor) as b, \
             patch(__name__ + '.compare_plan', return_value=compare) as c, \
             patch(__name__ + '.copy_plan', return_value=copy) as d, \
             patch(__name__ + '.immediate_plan', return_value=immediate) as e, \
             patch(__name__ + '.signext_plan', return_value=signext) as f, \
             patch(__name__ + '.second_immediate_plan', return_value=second) as g, \
             patch(__name__ + '.third_immediate_plan', return_value=third) as h:
            self.assertEqual(plan(b'dol', b'elf')[0], 'integer')
        b.assert_called_once_with(b'dol', b'elf', with_live=True)
        c.assert_called_once_with(b'dol', b'elf', predecessor=predecessor)
        d.assert_called_once_with(
            b'dol', b'elf', predecessor=predecessor, compare=compare)
        e.assert_called_once_with(
            b'dol', b'elf', predecessor=predecessor,
            compare=compare, copy=copy)
        f.assert_called_once_with(
            b'dol', b'elf', predecessor=predecessor, compare=compare,
            copy=copy, immediate=immediate)
        g.assert_called_once_with(
            b'dol', b'elf', predecessor=predecessor, compare=compare,
            copy=copy, immediate=immediate, signext=signext)
        h.assert_called_once_with(
            b'dol', b'elf', predecessor=predecessor, compare=compare,
            copy=copy, immediate=immediate, signext=signext, second=second)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('dol', type=Path, nargs='?')
    parser.add_argument('elf', type=Path, nargs='?')
    parser.add_argument('--self-test', action='store_true')
    q = parser.parse_args()
    if q.self_test:
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
        return (0 if unittest.TextTestRunner(verbosity=2)
                .run(suite).wasSuccessful() else 1)
    safe = {
        'size', 'next third immediate contract',
        'next third immediate provenance', 'next third immediate state',
    }
    try:
        if (q.dol is None or q.elf is None or
                not 256 <= q.dol.stat().st_size <= MAX_DOL or
                not 52 <= q.elf.stat().st_size <= 64 * 1024 * 1024):
            raise ValueError('size')
        with plan_cache_scope():
            family, name, counts, modeled, reason = plan(
                q.dol.read_bytes(), q.elf.read_bytes())
    except (OSError, ValueError, TypeError, KeyError, IndexError,
            struct.error) as error:
        msg = str(error)
        print('FORMATTER_125_PROVENANCE verified=0 reason=' +
              (msg.replace(' ', '_') if msg in safe else 'private_input'))
        return 1
    reads, writes, constant, stack, partial, other, cr, carry, xer, oe, alias = counts
    print(
        f'FORMATTER_125_PROVENANCE verified=1 previous_124_fixture=1 '
        f'next_original_word=1 family={family} operation={name} '
        f'reads={reads} writes={writes} constant_inputs={constant} '
        f'stack_inputs={stack} partial_inputs={partial} '
        f'other_inputs={other} condition_write={cr} carry_read={carry} '
        f'xer_write={xer} overflow_enable={oe} alias={alias} '
        f'gpr_model={modeled} reason={reason.replace(" ", "_")} '
        'original_execution=0'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
