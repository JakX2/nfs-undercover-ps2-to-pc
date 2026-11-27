#!/usr/bin/env python3
"""Private read-only classification of original instruction 121.

Only the guarded 120th-instruction fixture is inspected. No guest instruction
is executed and no original address, word, operand value or game bytes are
printed. Keep this separate from a genuine 120 native-execution milestone.
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
from prepare_formatter_report_compare_fixture import plan as compare_plan, promote as promote_compare
from prepare_formatter_report_stack_copy_fixture import plan as copy_plan, promote as promote_copy
from prepare_v419_full_start import MAX_DOL
from private_plan_cache import plan_cache_scope

_ALLOWED_REASONS = frozenset({
    'caller integer opcode', 'caller integer encoding',
    'caller integer effects', 'caller integer inputs',
    'caller integer registers',
})


def inspect(copy, predecessor, compare):
    """Authenticate the full byte/compare/copy history before reading 121."""
    if (not isinstance(copy, tuple) or len(copy) != 2 or
            not isinstance(copy[1], tuple) or len(copy[1]) != 9 or
            not isinstance(predecessor, tuple) or len(predecessor) != 3):
        raise ValueError('next copy contract')
    root, pc, word, next_pc, next_word, src, dst, offset, ret = copy[1]
    if (type(next_word) is not int or not 0 <= next_word <= 0xffffffff or
            next_word == GUARD):
        raise ValueError('next copy contract')
    # Reconstruct the prior fixture from the same authenticated predecessor.
    # This rejects a changed original word, guard, return, root, source, offset
    # or sibling block before any candidate successor is classified.
    try:
        expected = promote_copy(compare, predecessor, next_word)
    except (ValueError, TypeError, IndexError, KeyError) as error:
        raise ValueError('next copy provenance') from error
    if copy != expected or pc != root + 8 or next_pc != root + 12:
        raise ValueError('next copy contract')
    byte, regs, mask = predecessor
    if (not isinstance(regs, (tuple, list)) or len(regs) != 32 or
            type(mask) is not int or not 0 <= mask <= 0xffffffff):
        raise ValueError('next copy state')
    after = list(regs)
    load = byte[1][1]
    value = byte[1][4]
    after[(load >> 21) & 31] = ('const', value)
    after_compare, _ = step(byte[1][6], tuple(after), saved_mask=mask)
    after_copy, inputs = step(word, after_compare, saved_mask=mask,
                              allow_stack_copy=True)
    if inputs or after_copy[dst] != after_compare[src] or (
            after_copy[1][0] != 'stack'):
        raise ValueError('next copy state')
    family = boundary_shape(next_word)
    if family != 'integer':
        return family, 'not_integer', (0,) * 11, 0, 'not_attempted'
    name, reads, writes, cr, carry, xer, oe = classify(next_word)
    read_set, write_set = set(reads), set(writes)
    kinds = Counter(after_copy[i][0] for i in read_set)
    counts = (
        len(read_set), len(write_set), kinds['const'], kinds['stack'],
        kinds['partial'], len(read_set)-kinds['const']-kinds['stack']-kinds['partial'],
        cr, carry, xer, oe, int(bool(read_set & write_set)),
    )
    try:
        modeled, _ = step(next_word, after_copy, saved_mask=mask,
                          allow_stack_copy=True)
        if len(modeled) != 32:
            raise ValueError('caller integer registers')
        reason = 'supported'
    except ValueError as error:
        modeled = None
        reason = str(error) if str(error) in _ALLOWED_REASONS else 'not_modelled'
    return family, name, counts, int(modeled is not None), reason


def plan(dol, elf):
    predecessor = byte_plan(dol, elf, with_live=True)
    compare = compare_plan(dol, elf, predecessor=predecessor)
    copy = copy_plan(dol, elf, predecessor=predecessor, compare=compare)
    return inspect(copy, predecessor, compare)


class Tests(unittest.TestCase):
    def setUp(self):
        self.root = 0x80010000
        self.load = (34 << 26) | (9 << 21) | (7 << 16) | 1
        self.cmp = (11 << 26) | (3 << 23) | (7 << 16) | 0x8000
        self.move = (31 << 26) | (1 << 21) | (10 << 16) | (1 << 11) | (444 << 1)
        self.next = (14 << 26) | (11 << 21) | (10 << 16) | 4
        self.byte = ({self.root: (self.load, self.cmp, GUARD)},
                     (self.root, self.load, 753, 17, 0x5a,
                      self.root + 4, self.cmp, self.root + 0x100))
        self.regs = [('reg', i) for i in range(32)]
        self.regs[1] = ('stack', -864)
        self.regs[7] = ('const', 0x81234567)

    def inputs(self, next_word=None):
        predecessor = (self.byte, tuple(self.regs), 0)
        compare = promote_compare(self.byte, self.move, (7, 0x81234567))
        copy = promote_copy(compare, predecessor,
                            self.next if next_word is None else next_word)
        return copy, predecessor, compare

    def test_stack_arithmetic_is_visible_but_not_synthesized(self):
        family, name, counts, modeled, reason = inspect(*self.inputs())
        self.assertEqual((family, name, modeled, reason),
                         ('integer', 'add_immediate', 0, 'caller integer inputs'))
        self.assertEqual(counts, (1, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0))

    def test_constant_byte_and_comparison_are_independently_modelable(self):
        following = (14 << 26) | (11 << 21) | (9 << 16) | 1
        self.assertEqual(inspect(*self.inputs(following))[3:], (1, 'supported'))
        following = (10 << 26) | (3 << 23) | (7 << 16) | 0x8000
        family, name, counts, modeled, reason = inspect(*self.inputs(following))
        self.assertEqual((family, name, modeled, reason),
                         ('integer', 'compare_immediate', 1, 'supported'))
        self.assertEqual((counts[1], counts[2], counts[6]), (0, 1, 1))

    def test_branch_is_only_classified(self):
        following = (16 << 26) | (12 << 21) | (2 << 16) | 16
        family, name, counts, modeled, reason = inspect(*self.inputs(following))
        self.assertEqual((family, name, counts, modeled, reason),
                         ('branch', 'not_integer', (0,) * 11, 0, 'not_attempted'))

    def test_opaque_register_is_not_concretized(self):
        following = (14 << 26) | (11 << 21) | (8 << 16) | 1
        _, _, counts, modeled, reason = inspect(*self.inputs(following))
        self.assertEqual((counts[5], modeled, reason),
                         (1, 0, 'caller integer inputs'))

    def test_copy_and_predecessor_tampering_is_refused(self):
        copy, predecessor, compare = self.inputs()
        blocks, fields = copy
        for bad in (
            ({**blocks, self.root: blocks[self.root][:-1] + (0,)}, fields),
            (blocks, fields[:-2] + (1,) + fields[-1:]),
            (blocks, fields[:4] + (GUARD,) + fields[5:]),
            (blocks, fields[:5] + (7,) + fields[6:]),
        ):
            with self.subTest(bad=bad[1]):
                with self.assertRaises(ValueError):
                    inspect(bad, predecessor, compare)
        bad_reg = list(self.regs)
        bad_reg[7] = ('reg', 7)
        with self.assertRaises(ValueError):
            inspect(copy, (self.byte, tuple(bad_reg), 0), compare)
        with self.assertRaises(ValueError):
            inspect(copy, (), compare)

    def test_shared_predecessor_snapshot_and_no_reexecution(self):
        expected = self.inputs()
        with patch(__name__ + '.byte_plan', return_value=expected[1]) as b, \
             patch(__name__ + '.compare_plan', return_value=expected[2]) as c, \
             patch(__name__ + '.copy_plan', return_value=expected[0]) as d:
            result = plan(b'private fixture', b'elf')
        b.assert_called_once_with(b'private fixture', b'elf', with_live=True)
        c.assert_called_once_with(b'private fixture', b'elf',
                                  predecessor=expected[1])
        d.assert_called_once_with(b'private fixture', b'elf',
                                  predecessor=expected[1], compare=expected[2])
        self.assertEqual(result[0], 'integer')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('dol', type=Path, nargs='?')
    parser.add_argument('elf', type=Path, nargs='?')
    parser.add_argument('--self-test', action='store_true')
    q = parser.parse_args()
    if q.self_test:
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
        return 0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1
    safe = {'size', 'next copy contract', 'next copy provenance', 'next copy state'}
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
        print('FORMATTER_121_PROVENANCE verified=0 reason=' +
              (msg.replace(' ', '_') if msg in safe else 'private_input'))
        return 1
    reads, writes, constant, stack, partial, other, cr, carry, xer, oe, alias = counts
    print(f'FORMATTER_121_PROVENANCE verified=1 previous_120_fixture=1 '
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
