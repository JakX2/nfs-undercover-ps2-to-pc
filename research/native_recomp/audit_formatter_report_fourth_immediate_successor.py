#!/usr/bin/env python3
"""Read-only, fail-closed provenance of original formatter instruction 126.

Authenticate the original 118–125 chain before classifying its next word.
Never translate, interpret, or execute original instruction 126; never print
original words, guest addresses, operands, or register values.
"""
import argparse
import struct
import unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch

from audit_formatter_partial_copy import boundary_shape
from audit_formatter_partial_integer import classify
from audit_formatter_report_third_immediate_successor import Tests as AuditInputs
from guarded_continuation import GUARD
from prepare_formatter_caller_integer_contract import step
from prepare_formatter_next_entry_report_byte_contract import plan as byte_plan
from prepare_formatter_report_compare_fixture import plan as compare_plan
from prepare_formatter_report_stack_copy_fixture import plan as copy_plan
from prepare_formatter_report_immediate_fixture import plan as immediate_plan
from prepare_formatter_report_signext_fixture import plan as signext_plan
from prepare_formatter_report_post_signext_immediate_fixture import plan as second_plan
from prepare_formatter_report_third_immediate_fixture import plan as third_plan
from prepare_formatter_report_fourth_immediate_fixture import (
    plan as fourth_plan, promote as promote_fourth,
)
from prepare_v419_full_start import MAX_DOL
from private_plan_cache import plan_cache_scope

_ALLOWED = frozenset({
    'caller integer opcode', 'caller integer encoding',
    'caller integer effects', 'caller integer inputs',
    'caller integer registers',
})


def inspect(fourth, third, second, signext, immediate, copy, predecessor, compare):
    """Authenticate all prior words and symbolically classify original 126."""
    if (not isinstance(fourth, tuple) or len(fourth) != 2 or
            not isinstance(fourth[1], tuple) or len(fourth[1]) != 8 or
            not isinstance(predecessor, tuple) or len(predecessor) != 3):
        raise ValueError('next fourth immediate contract')
    root, pc, word, next_pc, next_word, dst, value, ret = fourth[1]
    if (type(next_word) is not int or
            not 0 <= next_word <= 0xffffffff or next_word == GUARD):
        raise ValueError('next fourth immediate contract')
    try:
        expected = promote_fourth(
            third, second, signext, immediate, copy, predecessor, compare,
            next_word)
        if (fourth != expected or pc != root + 28 or
                next_pc != root + 32 or ret != third[1][7]):
            raise ValueError('contract mismatch')
    except (ValueError, KeyError, TypeError, IndexError) as error:
        raise ValueError('next fourth immediate provenance') from error

    byte, regs, saved = predecessor
    if (not isinstance(regs, (tuple, list)) or len(regs) != 32 or
            type(saved) is not int or not 0 <= saved <= 0xffffffff):
        raise ValueError('next fourth immediate state')
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
            third[1][2], after_123, saved_mask=saved)
        after_125, fourth_inputs = step(
            word, after_124, saved_mask=saved)
        if (copy_inputs or first_inputs or second_inputs or third_inputs or
                fourth_inputs or
                signed_inputs != ((signext[1][5], signext[1][6]),) or
                after_122[signext[1][5]] != ('const', signext[1][7]) or
                after_123[second[1][5]] != ('const', second[1][6]) or
                after_124[third[1][5]] != ('const', third[1][6]) or
                after_125[dst] != ('const', value) or
                after_125[1][0] != 'stack' or len(after_125) != 32):
            raise ValueError('state mismatch')
    except (ValueError, TypeError, IndexError, KeyError) as error:
        raise ValueError('next fourth immediate state') from error

    family = boundary_shape(next_word)
    if family != 'integer':
        return family, 'not_integer', (0,) * 11, 0, 'not_attempted'
    name, reads, writes, cr, carry, xer, oe = classify(next_word)
    read_set, write_set = set(reads), set(writes)
    kinds = Counter(after_125[i][0] for i in read_set)
    counts = (
        len(read_set), len(write_set), kinds['const'], kinds['stack'],
        kinds['partial'], len(read_set) -
        kinds['const'] - kinds['stack'] - kinds['partial'],
        cr, carry, xer, oe, int(bool(read_set & write_set)),
    )
    try:
        modeled, _ = step(
            next_word, after_125, saved_mask=saved,
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
        dol, elf, predecessor=predecessor,
        compare=compare, copy=copy, immediate=immediate)
    second = second_plan(
        dol, elf, predecessor=predecessor, compare=compare, copy=copy,
        immediate=immediate, signext=signext)
    third = third_plan(
        dol, elf, predecessor=predecessor, compare=compare, copy=copy,
        immediate=immediate, signext=signext, second=second)
    fourth = fourth_plan(
        dol, elf, predecessor=predecessor, compare=compare, copy=copy,
        immediate=immediate, signext=signext, second=second, third=third)
    return inspect(
        fourth, third, second, signext, immediate, copy, predecessor, compare)


class Tests(unittest.TestCase):
    def setUp(self):
        self.base = AuditInputs('test_instruction_124_result_reaches_next_input')
        self.base.setUp()
        self.fourth_word = self.base.base.addi(6, 0, 0xff80)

    def inputs(self, next_word=None, source=9, fourth_word=None):
        third, second, signext, immediate, copy, predecessor, compare = (
            self.base.inputs(
                next_word=self.fourth_word if fourth_word is None
                else fourth_word, source=source))
        next_word = (self.base.base.addi(5, 6, 1)
                     if next_word is None else next_word)
        fourth = promote_fourth(
            third, second, signext, immediate, copy, predecessor, compare,
            next_word)
        return (fourth, third, second, signext, immediate, copy,
                predecessor, compare)

    def test_instruction_125_result_reaches_126_input(self):
        result = inspect(*self.inputs())
        self.assertEqual((result[0], result[1], result[3:]),
                         ('integer', 'add_immediate', (1, 'supported')))
        self.assertEqual(result[2], (1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0))

    def test_alias_reads_125_result(self):
        result = inspect(*self.inputs(self.base.base.addi(6, 6, 1)))
        self.assertEqual(result[2], (1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1))
        self.assertEqual(result[3:], (1, 'supported'))

    def test_unknown_and_zero_inputs_are_distinct(self):
        zero = inspect(*self.inputs(self.base.base.addi(5, 0, 1)))
        unknown = inspect(*self.inputs(self.base.base.addi(5, 8, 1)))
        self.assertEqual(zero[2][0], 0)
        self.assertEqual(zero[3:], (1, 'supported'))
        self.assertEqual((unknown[2][5], unknown[3], unknown[4]),
                         (1, 0, 'caller integer inputs'))

    def test_non_integer_is_never_executed(self):
        branch = (16 << 26) | (12 << 21) | (2 << 16) | 16
        self.assertEqual(inspect(*self.inputs(branch)),
                         ('branch', 'not_integer', (0,) * 11, 0,
                          'not_attempted'))

    def test_modified_predecessor_and_return_guard_rejected(self):
        full = self.inputs()
        fourth, *older = full
        blocks, fields = fourth
        root = fields[0]
        mutants = (
            ({**blocks, root: blocks[root][:-1] + (0,)}, fields),
            (blocks, fields[:4] + (GUARD,) + fields[5:]),
            (blocks, fields[:6] + (0,) + fields[7:]),
            (blocks, fields[:-1] + (root + 36,)),
        )
        for candidate in mutants:
            with self.subTest(candidate=candidate[1]):
                with self.assertRaises(ValueError):
                    inspect(candidate, *older)
        with self.assertRaises(ValueError):
            inspect((blocks, fields[:4] + (0x100000000,) + fields[5:]), *older)

    def test_plan_reuses_exact_125_authenticated_chain(self):
        full = self.inputs()
        fourth, third, second, signext, immediate, copy, predecessor, compare = full
        names = ('byte_plan', 'compare_plan', 'copy_plan', 'immediate_plan',
                 'signext_plan', 'second_plan', 'third_plan', 'fourth_plan')
        values = (predecessor, compare, copy, immediate, signext, second,
                  third, fourth)
        patches = [patch(__name__ + '.' + name, return_value=value)
                   for name, value in zip(names, values)]
        mocks = [item.start() for item in patches]
        try:
            self.assertEqual(plan(b'dol', b'elf')[0], 'integer')
        finally:
            for item in reversed(patches):
                item.stop()
        for mock in mocks:
            mock.assert_called_once()


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
        'size', 'next fourth immediate contract',
        'next fourth immediate provenance', 'next fourth immediate state',
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
        print('FORMATTER_126_PROVENANCE verified=0 reason=' +
              (msg.replace(' ', '_') if msg in safe else 'private_input'))
        return 1
    reads, writes, constant, stack, partial, other, cr, carry, xer, oe, alias = counts
    print(
        f'FORMATTER_126_PROVENANCE verified=1 previous_125_fixture=1 '
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
