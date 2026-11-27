#!/usr/bin/env python3
"""Read-only, fail-closed classification of original formatter instruction 122.

Reconstruct the original 118 byte load, 119 compare, 120 stack copy,
and authenticated 121 zero-input PPC addi. The following original word is
classified and optionally modeled, never executed. No instruction bits,
addresses, operands, or translated source leave the private owner.
"""
import argparse
import struct
import unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch

from audit_formatter_partial_copy import boundary_shape
from audit_formatter_partial_integer import classify
from guarded_continuation import GUARD
from prepare_formatter_caller_integer_contract import step
from prepare_formatter_next_entry_report_byte_contract import plan as byte_plan
from prepare_formatter_report_compare_fixture import (
    plan as compare_plan, promote as promote_compare,
)
from prepare_formatter_report_stack_copy_fixture import (
    plan as copy_plan, promote as promote_copy,
)
from prepare_formatter_report_immediate_fixture import (
    plan as immediate_plan, promote as promote_immediate,
)
from prepare_v419_full_start import MAX_DOL
from private_plan_cache import plan_cache_scope

_ALLOWED_REASONS = frozenset({
    'caller integer opcode', 'caller integer encoding',
    'caller integer effects', 'caller integer inputs',
    'caller integer registers',
})


def inspect(immediate, copy, predecessor, compare):
    """Authenticate the exact original 121 contract before inspecting 122."""
    if (not isinstance(immediate, tuple) or len(immediate) != 2 or
            not isinstance(immediate[1], tuple) or len(immediate[1]) != 8 or
            not isinstance(copy, tuple) or len(copy) != 2 or
            not isinstance(predecessor, tuple) or len(predecessor) != 3):
        raise ValueError('next immediate contract')
    root, pc, word, next_pc, next_word, dst, value, ret = immediate[1]
    if (type(next_word) is not int or
            not 0 <= next_word <= 0xffffffff or next_word == GUARD):
        raise ValueError('next immediate contract')
    try:
        expected = promote_immediate(copy, predecessor, compare, next_word)
    except (ValueError, TypeError, IndexError, KeyError) as error:
        raise ValueError('next immediate provenance') from error
    if (immediate != expected or pc != root + 12 or
            next_pc != root + 16 or ret != copy[1][8]):
        raise ValueError('next immediate contract')
    byte, regs, saved = predecessor
    if (not isinstance(regs, (tuple, list)) or len(regs) != 32 or
            type(saved) is not int or not 0 <= saved <= 0xffffffff):
        raise ValueError('next immediate state')
    try:
        after = list(regs)
        load, byte_value = byte[1][1], byte[1][4]
        after[(load >> 21) & 31] = ('const', byte_value)
        after_compare, _ = step(byte[1][6], tuple(after), saved_mask=saved)
        after_copy, copy_inputs = step(
            copy[1][2], after_compare,
            saved_mask=saved, allow_stack_copy=True)
        after_immediate, immediate_inputs = step(
            word, after_copy, saved_mask=saved)
        if (copy_inputs or immediate_inputs or
                after_immediate[dst] != ('const', value) or
                after_immediate[1][0] != 'stack' or
                len(after_immediate) != 32):
            raise ValueError('state mismatch')
    except (ValueError, TypeError, IndexError, KeyError) as error:
        raise ValueError('next immediate state') from error
    family = boundary_shape(next_word)
    if family != 'integer':
        return family, 'not_integer', (0,) * 11, 0, 'not_attempted'
    name, reads, writes, cr, carry, xer, oe = classify(next_word)
    read_set, write_set = set(reads), set(writes)
    kinds = Counter(after_immediate[i][0] for i in read_set)
    counts = (
        len(read_set), len(write_set), kinds['const'], kinds['stack'],
        kinds['partial'], len(read_set)-kinds['const']-kinds['stack']-kinds['partial'],
        cr, carry, xer, oe, int(bool(read_set & write_set)),
    )
    try:
        modeled, _ = step(next_word, after_immediate, saved_mask=saved,
                          allow_stack_copy=True, allow_stack_relative=True)
        if len(modeled) != 32:
            raise ValueError('caller integer registers')
        reason = 'supported'
    except ValueError as error:
        modeled = None
        reason = (str(error) if str(error) in _ALLOWED_REASONS
                  else 'not_modelled')
    return family, name, counts, int(modeled is not None), reason


def plan(dol, elf):
    predecessor = byte_plan(dol, elf, with_live=True)
    compare = compare_plan(dol, elf, predecessor=predecessor)
    copy = copy_plan(dol, elf, predecessor=predecessor, compare=compare)
    immediate = immediate_plan(
        dol, elf, predecessor=predecessor, compare=compare, copy=copy)
    return inspect(immediate, copy, predecessor, compare)


class Tests(unittest.TestCase):
    def setUp(self):
        self.root = 0x80010000
        self.load = (34 << 26) | (9 << 21) | (7 << 16) | 1
        self.cmp = (11 << 26) | (3 << 23) | (7 << 16) | 0x8000
        self.copy_word = ((31 << 26) | (1 << 21) | (10 << 16) |
                          (1 << 11) | (444 << 1))
        self.imm = (14 << 26) | (3 << 21) | 0xfffe
        self.next = (14 << 26) | (11 << 21) | (3 << 16) | 4
        self.byte = ({self.root: (self.load, self.cmp, GUARD)},
                     (self.root, self.load, 753, 17, 0x5a,
                      self.root + 4, self.cmp, self.root + 0x100))
        self.regs = [('reg', i) for i in range(32)]
        self.regs[1] = ('stack', -864)
        self.regs[7] = ('const', 0x81234567)

    def inputs(self, following=None):
        predecessor = (self.byte, tuple(self.regs), 0)
        compare = promote_compare(self.byte, self.copy_word,
                                  (7, 0x81234567))
        copy = promote_copy(compare, predecessor, self.imm)
        immediate = promote_immediate(
            copy, predecessor, compare,
            self.next if following is None else following)
        return immediate, copy, predecessor, compare

    def test_constant_written_by_121_is_symbolic_input_to_122(self):
        family, name, counts, modeled, reason = inspect(*self.inputs())
        self.assertEqual((family, name, modeled, reason),
                         ('integer', 'add_immediate', 1, 'supported'))
        self.assertEqual(counts, (1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0))

    def test_unrelated_unknown_remains_unknown(self):
        word = (14 << 26) | (11 << 21) | (8 << 16) | 1
        family, name, counts, modeled, reason = inspect(*self.inputs(word))
        self.assertEqual((family, name, counts[5], modeled, reason),
                         ('integer', 'add_immediate', 1, 0,
                          'caller integer inputs'))

    def test_stack_copy_remains_proven_without_concrete_pointer(self):
        word = ((31 << 26) | (10 << 21) | (11 << 16) |
                (10 << 11) | (444 << 1))
        family, name, counts, modeled, reason = inspect(*self.inputs(word))
        self.assertEqual((family, name, counts[3], modeled, reason),
                         ('integer', 'or', 1, 1, 'supported'))

    def test_branch_is_classified_not_executed(self):
        word = (16 << 26) | (12 << 21) | (2 << 16) | 16
        family, name, counts, modeled, reason = inspect(*self.inputs(word))
        self.assertEqual((family, name, counts, modeled, reason),
                         ('branch', 'not_integer', (0,) * 11, 0,
                          'not_attempted'))

    def test_full_predecessor_and_guard_tampering_refused(self):
        immediate, copy, predecessor, compare = self.inputs()
        blocks, fields = immediate
        forged = (
            ({**blocks, self.root: blocks[self.root][:-1] + (0,)}, fields),
            (blocks, fields[:4] + (GUARD,) + fields[5:]),
            (blocks, fields[:5] + (4,) + fields[6:]),
            (blocks, fields[:-1] + (self.root + 20,)),
        )
        for alteration in forged:
            with self.subTest(alteration=alteration[1]):
                with self.assertRaises(ValueError):
                    inspect(alteration, copy, predecessor, compare)
        bad_reg = list(self.regs)
        bad_reg[7] = ('reg', 7)
        with self.assertRaises(ValueError):
            inspect(immediate, copy,
                    (self.byte, tuple(bad_reg), 0), compare)
        with self.assertRaises(ValueError):
            inspect(immediate, copy, (), compare)

    def test_plan_reuses_authenticated_predecessor(self):
        immediate, copy, predecessor, compare = self.inputs()
        with patch(__name__ + '.byte_plan',return_value=predecessor) as b, \
             patch(__name__ + '.compare_plan',return_value=compare) as c, \
             patch(__name__ + '.copy_plan',return_value=copy) as d, \
             patch(__name__ + '.immediate_plan',return_value=immediate) as e:
            result = plan(b'private fixture', b'elf')
        b.assert_called_once_with(b'private fixture',b'elf',with_live=True)
        c.assert_called_once_with(b'private fixture',b'elf',
                                  predecessor=predecessor)
        d.assert_called_once_with(b'private fixture',b'elf',
                                  predecessor=predecessor,compare=compare)
        e.assert_called_once_with(b'private fixture',b'elf',
                                  predecessor=predecessor,compare=compare,
                                  copy=copy)
        self.assertEqual(result[0],'integer')


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
        'size', 'next immediate contract', 'next immediate provenance',
        'next immediate state',
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
        print('FORMATTER_122_PROVENANCE verified=0 reason=' +
              (msg.replace(' ', '_') if msg in safe else 'private_input'))
        return 1
    reads, writes, constant, stack, partial, other, cr, carry, xer, oe, alias = counts
    print(f'FORMATTER_122_PROVENANCE verified=1 previous_121_fixture=1 '
          f'next_original_word=1 family={family} operation={name} '
          f'reads={reads} writes={writes} constant_inputs={constant} '
          f'stack_inputs={stack} partial_inputs={partial} '
          f'other_inputs={other} condition_write={cr} carry_read={carry} '
          f'xer_write={xer} overflow_enable={oe} alias={alias} '
          f'gpr_model={modeled} reason={reason.replace(" ", "_")} '
          f'original_execution=0')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
