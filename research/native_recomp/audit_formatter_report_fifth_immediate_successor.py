#!/usr/bin/env python3
"""Read-only, fail-closed provenance of original formatter instruction 127.

Authenticate the original 118–126 path from an independently captured
symbolic state before classifying original 127. Never translate, interpret,
or execute 127; never print game instructions, addresses or register values.
"""
import argparse
import struct
import unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch

from audit_formatter_partial_copy import boundary_shape
from audit_formatter_partial_integer import classify
from audit_formatter_report_fourth_immediate_successor import Tests as AuditInputs
from guarded_continuation import GUARD
from prepare_formatter_caller_integer_contract import step
from prepare_formatter_next_entry_report_byte_contract import plan as byte_plan
from prepare_formatter_report_compare_fixture import plan as compare_plan
from prepare_formatter_report_stack_copy_fixture import plan as copy_plan
from prepare_formatter_report_immediate_fixture import plan as immediate_plan
from prepare_formatter_report_signext_fixture import plan as signext_plan
from prepare_formatter_report_post_signext_immediate_fixture import plan as second_plan
from prepare_formatter_report_third_immediate_fixture import plan as third_plan
from prepare_formatter_report_fourth_immediate_fixture import plan as fourth_plan
from prepare_formatter_report_fifth_immediate_fixture import (
    plan as fifth_plan, promote as promote_fifth,
)
from prepare_v419_full_start import MAX_DOL
from private_plan_cache import plan_cache_scope

_ALLOWED = frozenset({
    'caller integer opcode', 'caller integer encoding',
    'caller integer effects', 'caller integer inputs',
    'caller integer registers',
})


def inspect(fifth, fourth, third, second, signext, immediate, copy,
            predecessor, compare):
    """Authenticate all prior original words before classifying original 127."""
    if (not isinstance(fifth, tuple) or len(fifth) != 2 or
            not isinstance(fifth[1], tuple) or len(fifth[1]) != 8 or
            not isinstance(predecessor, tuple) or len(predecessor) != 3):
        raise ValueError('next fifth immediate contract')
    root, pc, word, next_pc, next_word, dst, value, ret = fifth[1]
    if (type(next_word) is not int or
            not 0 <= next_word <= 0xffffffff or next_word == GUARD):
        raise ValueError('next fifth immediate contract')
    try:
        expected = promote_fifth(
            fourth, third, second, signext, immediate, copy,
            predecessor, compare, next_word)
        if (fifth != expected or pc != root + 32 or
                next_pc != root + 36 or ret != fourth[1][7]):
            raise ValueError('contract mismatch')
    except (ValueError, KeyError, TypeError, IndexError) as error:
        raise ValueError('next fifth immediate provenance') from error

    byte, regs, saved = predecessor
    if (not isinstance(regs, (tuple, list)) or len(regs) != 32 or
            type(saved) is not int or not 0 <= saved <= 0xffffffff):
        raise ValueError('next fifth immediate state')
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
            fourth[1][2], after_124, saved_mask=saved)
        after_126, fifth_inputs = step(
            word, after_125, saved_mask=saved)
        if (copy_inputs or first_inputs or second_inputs or third_inputs or
                fourth_inputs or fifth_inputs or
                signed_inputs != ((signext[1][5], signext[1][6]),) or
                after_122[signext[1][5]] != ('const', signext[1][7]) or
                after_123[second[1][5]] != ('const', second[1][6]) or
                after_124[third[1][5]] != ('const', third[1][6]) or
                after_125[fourth[1][5]] != ('const', fourth[1][6]) or
                after_126[dst] != ('const', value) or
                after_126[1][0] != 'stack' or len(after_126) != 32):
            raise ValueError('state mismatch')
    except (ValueError, TypeError, IndexError, KeyError) as error:
        raise ValueError('next fifth immediate state') from error

    family = boundary_shape(next_word)
    if family != 'integer':
        return family, 'not_integer', (0,) * 11, 0, 'not_attempted'
    name, reads, writes, cr, carry, xer, oe = classify(next_word)
    read_set, write_set = set(reads), set(writes)
    kinds = Counter(after_126[i][0] for i in read_set)
    counts = (
        len(read_set), len(write_set), kinds['const'], kinds['stack'],
        kinds['partial'], len(read_set) -
        kinds['const'] - kinds['stack'] - kinds['partial'],
        cr, carry, xer, oe, int(bool(read_set & write_set)),
    )
    try:
        modeled, _ = step(
            next_word, after_126, saved_mask=saved,
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
    second = second_plan(
        dol, elf, predecessor=predecessor, compare=compare, copy=copy,
        immediate=immediate, signext=signext)
    third = third_plan(
        dol, elf, predecessor=predecessor, compare=compare, copy=copy,
        immediate=immediate, signext=signext, second=second)
    fourth = fourth_plan(
        dol, elf, predecessor=predecessor, compare=compare, copy=copy,
        immediate=immediate, signext=signext, second=second, third=third)
    fifth = fifth_plan(
        dol, elf, predecessor=predecessor, compare=compare, copy=copy,
        immediate=immediate, signext=signext, second=second, third=third,
        fourth=fourth)
    return inspect(
        fifth, fourth, third, second, signext, immediate, copy,
        predecessor, compare)


class Tests(unittest.TestCase):
    def setUp(self):
        self.base = AuditInputs('test_instruction_125_result_reaches_126_input')
        self.base.setUp()
        self.fifth_word = self.base.base.base.addi(5, 0, 0xff80)

    def inputs(self, next_word=None, source=9, fifth_word=None):
        fourth, third, second, signext, immediate, copy, predecessor, compare = (
            self.base.inputs(
                next_word=self.fifth_word if fifth_word is None else fifth_word,
                source=source))
        next_word = (self.base.base.base.addi(7, 5, 1)
                     if next_word is None else next_word)
        fifth = promote_fifth(
            fourth, third, second, signext, immediate, copy,
            predecessor, compare, next_word)
        return (fifth, fourth, third, second, signext, immediate, copy,
                predecessor, compare)

    def test_instruction_126_constant_reaches_next_original_input(self):
        result = inspect(*self.inputs())
        self.assertEqual((result[0], result[1], result[3:]),
                         ('integer', 'add_immediate', (1, 'supported')))
        self.assertEqual(result[2], (1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0))

    def test_alias_reads_126_result(self):
        following = self.base.base.base.addi(5, 5, 1)
        result = inspect(*self.inputs(following))
        self.assertEqual(result[2], (1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1))

    def test_zero_and_unknown_inputs_differ(self):
        zero = inspect(*self.inputs(self.base.base.base.addi(7, 0, 1)))
        unknown = inspect(*self.inputs(self.base.base.base.addi(7, 8, 1)))
        self.assertEqual(zero[2][0], 0)
        self.assertEqual(zero[3:], (1, 'supported'))
        self.assertEqual((unknown[2][5], unknown[3], unknown[4]),
                         (1, 0, 'caller integer inputs'))

    def test_branch_is_classified_never_executed(self):
        branch = (16 << 26) | (12 << 21) | (2 << 16) | 16
        self.assertEqual(inspect(*self.inputs(branch)),
                         ('branch', 'not_integer', (0,) * 11, 0,
                          'not_attempted'))

    def test_full_signed_byte_range_remains_authenticated(self):
        for low in range(256):
            with self.subTest(low=low):
                self.base.base.base.base.imm = (
                    self.base.base.base.addi(3, 0, low))
                result = inspect(*self.inputs(source=3))
                self.assertEqual(result[2][2:6], (1, 0, 0, 0))
                self.assertEqual(result[3:], (1, 'supported'))

    def test_corrupt_guard_and_earlier_return_alias_refused(self):
        full = self.inputs()
        fifth, *older = full
        blocks, fields = fifth
        root = fields[0]
        mutants = (
            ({**blocks, root: blocks[root][:-1] + (0,)}, fields),
            (blocks, fields[:4] + (GUARD,) + fields[5:]),
            (blocks, fields[:6] + (0,) + fields[7:]),
            (blocks, fields[:-1] + (root + 40,)),
        )
        for candidate in mutants:
            with self.subTest(candidate=candidate[1]):
                with self.assertRaises(ValueError):
                    inspect(candidate, *older)

    def test_plan_passes_fully_authenticated_predecessors(self):
        fifth, fourth, third, second, signext, immediate, copy, predecessor, compare = (
            self.inputs())
        names = ('byte_plan', 'compare_plan', 'copy_plan', 'immediate_plan',
                 'signext_plan', 'second_plan', 'third_plan',
                 'fourth_plan', 'fifth_plan')
        values = (predecessor, compare, copy, immediate, signext,
                  second, third, fourth, fifth)
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
        'size', 'next fifth immediate contract',
        'next fifth immediate provenance', 'next fifth immediate state',
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
        print('FORMATTER_127_PROVENANCE verified=0 reason=' +
              (msg.replace(' ', '_') if msg in safe else 'private_input'))
        return 1
    reads, writes, constant, stack, partial, other, cr, carry, xer, oe, alias = counts
    print(
        f'FORMATTER_127_PROVENANCE verified=1 previous_126_fixture=1 '
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
