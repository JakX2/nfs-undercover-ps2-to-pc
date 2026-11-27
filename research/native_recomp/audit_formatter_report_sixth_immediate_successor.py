#!/usr/bin/env python3
"""Read-only, fail-closed provenance of original formatter instruction 128.

Authenticate original 118–127 using the complete predecessor fixtures, then
classify the next authentic word. No guest code executes or is published.
"""
import argparse
import struct
import subprocess
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch

from audit_formatter_partial_copy import boundary_shape
from audit_formatter_partial_integer import classify
from audit_formatter_report_fifth_immediate_successor import Tests as AuditInputs
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
    plan as fifth_plan,
)
from prepare_v419_full_start import MAX_DOL
from private_plan_cache import plan_cache_scope
from prepare_formatter_report_sixth_immediate_fixture import (
    plan as sixth_plan, promote as promote_sixth,
)

_ALLOWED = frozenset({
    'caller integer opcode', 'caller integer encoding',
    'caller integer effects', 'caller integer inputs',
    'caller integer registers',
})


def branch_shape(word):
    """Classify a stopped PPC branch without leaking PCs or targets.

    This classification never executes guest code. The eventual native
    continuation needs private target and CPU-state authentication too.
    """
    if type(word) is not int or not 0 <= word <= 0xffffffff:
        raise ValueError('branch word')
    op = word >> 26
    link = int(bool(word & 1))
    if op == 18:  # b / ba / bl / bla
        return 'direct', 0, 0, link, int(bool(word & 2)), 'immediate'
    if op == 16:  # bc family
        bo = (word >> 21) & 31
        return ('conditional_direct', int(not bool(bo & 0x10)),
                int(not bool(bo & 0x04)), link,
                int(bool(word & 2)), 'immediate')
    if op == 19:
        xo = (word >> 1) & 1023
        bo = (word >> 21) & 31
        if xo in (16, 528):
            cr = int(not bool(bo & 0x10))
            ctr = int(not bool(bo & 0x04))
            # bcctr forbids BO encodings which decrement CTR.
            if xo == 528 and ctr:
                return 'unsupported_ctr_branch', cr, ctr, link, 0, 'ctr'
            return ('conditional_lr' if xo == 16 else 'conditional_ctr',
                    cr, ctr, link, 0, 'lr' if xo == 16 else 'ctr')
    return 'unsupported_branch', 0, 0, link, 0, 'unknown'



def inspect(sixth, fifth, fourth, third, second, signext, immediate, copy,
            predecessor, compare):
    """Classify 128 only after validating the exact original 127 fixture."""
    if (not isinstance(sixth, tuple) or len(sixth) != 2 or
            not isinstance(sixth[1], tuple) or len(sixth[1]) != 8 or
            not isinstance(predecessor, tuple) or len(predecessor) != 3):
        raise ValueError('next sixth immediate contract')
    root, pc, word, next_pc, next_word, dst, value, ret = sixth[1]
    if (type(next_word) is not int or
            not 0 <= next_word <= 0xffffffff or next_word == GUARD):
        raise ValueError('next sixth immediate contract')
    try:
        expected = promote_sixth(
            fifth, fourth, third, second, signext, immediate, copy,
            predecessor, compare, next_word)
        if (sixth != expected or pc != root + 36 or
                next_pc != root + 40 or ret != fifth[1][7]):
            raise ValueError('contract mismatch')
    except (ValueError, KeyError, TypeError, IndexError) as error:
        raise ValueError('next sixth immediate provenance') from error

    byte, regs, saved = predecessor
    if (not isinstance(regs, (tuple, list)) or len(regs) != 32 or
            type(saved) is not int or not 0 <= saved <= 0xffffffff):
        raise ValueError('next sixth immediate state')
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
            fifth[1][2], after_125, saved_mask=saved)
        after_127, sixth_inputs = step(
            word, after_126, saved_mask=saved)
        if (copy_inputs or first_inputs or second_inputs or third_inputs or
                fourth_inputs or fifth_inputs or sixth_inputs or
                signed_inputs != ((signext[1][5], signext[1][6]),) or
                after_122[signext[1][5]] != ('const', signext[1][7]) or
                after_123[second[1][5]] != ('const', second[1][6]) or
                after_124[third[1][5]] != ('const', third[1][6]) or
                after_125[fourth[1][5]] != ('const', fourth[1][6]) or
                after_126[fifth[1][5]] != ('const', fifth[1][6]) or
                after_127[dst] != ('const', value) or
                after_127[1][0] != 'stack' or len(after_127) != 32):
            raise ValueError('state mismatch')
    except (ValueError, TypeError, IndexError, KeyError) as error:
        raise ValueError('next sixth immediate state') from error

    family = boundary_shape(next_word)
    if family != 'integer':
        return family, 'not_integer', (0,) * 11, 0, 'not_attempted'
    name, reads, writes, cr, carry, xer, oe = classify(next_word)
    read_set, write_set = set(reads), set(writes)
    kinds = Counter(after_127[i][0] for i in read_set)
    counts = (
        len(read_set), len(write_set), kinds['const'], kinds['stack'],
        kinds['partial'], len(read_set) -
        kinds['const'] - kinds['stack'] - kinds['partial'],
        cr, carry, xer, oe, int(bool(read_set & write_set)),
    )
    try:
        modeled, _ = step(
            next_word, after_127, saved_mask=saved,
            allow_stack_copy=True, allow_stack_relative=True)
        if len(modeled) != 32:
            raise ValueError('caller integer registers')
        reason = 'supported'
    except ValueError as error:
        modeled = None
        reason = (str(error) if str(error) in _ALLOWED
                  else 'not_modelled')
    return family, name, counts, int(modeled is not None), reason


def plan(dol, elf, *, with_branch=False):
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
    sixth = sixth_plan(
        dol, elf, predecessor=predecessor, compare=compare, copy=copy,
        immediate=immediate, signext=signext, second=second, third=third,
        fourth=fourth, fifth=fifth)
    summary = inspect(
        sixth, fifth, fourth, third, second, signext, immediate, copy,
        predecessor, compare)
    if with_branch:
        return (summary, branch_shape(sixth[1][4])
                if summary[0] == 'branch' else None)
    return summary


class Tests(unittest.TestCase):
    def setUp(self):
        self.base = AuditInputs('test_instruction_126_constant_reaches_next_original_input')
        self.base.setUp()

    @staticmethod
    def addi(dst, base, imm):
        return (14 << 26) | (dst << 21) | (base << 16) | (imm & 0xffff)

    def inputs(self, next_word=None, source=9, sixth_word=None):
        previous = self.base.inputs(
            next_word=self.addi(6, 0, 0x8000) if sixth_word is None else sixth_word,
            source=source)
        if next_word is None:
            next_word = self.addi(7, 6, 1)
        sixth = promote_sixth(*previous, next_word)
        return (sixth, *previous)

    def test_instruction_127_constant_reaches_128_input(self):
        self.assertEqual(inspect(*self.inputs()),
                         ('integer', 'add_immediate',
                          (1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0), 1, 'supported'))

    def test_alias_reads_127_result(self):
        self.assertEqual(inspect(*self.inputs(self.addi(6, 6, 1)))[2],
                         (1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1))

    def test_zero_and_unknown_inputs_differ(self):
        zero = inspect(*self.inputs(self.addi(7, 0, 1)))
        unknown = inspect(*self.inputs(self.addi(7, 8, 1)))
        self.assertEqual(zero[2][0], 0)
        self.assertEqual(zero[3:], (1, 'supported'))
        self.assertEqual((unknown[2][5], unknown[3], unknown[4]),
                         (1, 0, 'caller integer inputs'))

    def test_non_integer_is_never_executed(self):
        branch = (16 << 26) | (12 << 21) | (2 << 16) | 16
        self.assertEqual(inspect(*self.inputs(branch)),
                         ('branch', 'not_integer', (0,) * 11, 0, 'not_attempted'))

    def test_powerpc_branch_forms_are_abstracted_without_target_leak(self):
        forms = (
            (0x48000004, ('direct', 0, 0, 0, 0, 'immediate')),
            (0x48000007, ('direct', 0, 0, 1, 1, 'immediate')),
            ((16 << 26) | (12 << 21) | (2 << 16) | 16,
             ('conditional_direct', 1, 0, 0, 0, 'immediate')),
            ((16 << 26) | (16 << 21) | 16,
             ('conditional_direct', 0, 1, 0, 0, 'immediate')),
            (0x4e800020, ('conditional_lr', 0, 0, 0, 0, 'lr')),
            (0x4e800420, ('conditional_ctr', 0, 0, 0, 0, 'ctr')),
            ((19 << 26) | (16 << 21) | (528 << 1),
             ('unsupported_ctr_branch', 0, 1, 0, 0, 'ctr')),
        )
        for word, expected in forms:
            with self.subTest(word=word):
                self.assertEqual(branch_shape(word), expected)
        for word in (True, -1, 0x100000000, 'branch'):
            with self.assertRaises(ValueError):
                branch_shape(word)

    def test_signed_extremes_remain_authenticated(self):
        for imm in (0, 1, 0x7fff, 0x8000, 0xffff):
            for dst in (0, 3, 5, 6, 12):
                with self.subTest(imm=imm, dst=dst):
                    after = self.inputs(self.addi(7, dst, 1),
                                        sixth_word=self.addi(dst, 0, imm))
                    result = inspect(*after)
                    self.assertEqual(result[3:], (1, 'supported'))
                    self.assertEqual(result[2][2], int(dst != 0))

    def test_mutated_predecessor_and_return_alias_refused(self):
        sixth, *older = self.inputs()
        blocks, fields = sixth
        root = fields[0]
        mutants = (
            ({**blocks, root: blocks[root][:-1] + (0,)}, fields),
            ({**blocks, root: blocks[root][:2] + (0,) + blocks[root][3:]}, fields),
            (blocks, fields[:4] + (GUARD,) + fields[5:]),
            (blocks, fields[:6] + (0,) + fields[7:]),
            (blocks, fields[:-1] + (root + 44,)),
        )
        for candidate in mutants:
            with self.subTest(fields=candidate[1]):
                with self.assertRaises(ValueError):
                    inspect(candidate, *older)

    def test_invalid_128_lookaheads_never_authorize_execution(self):
        for word in (GUARD, -1, 0x100000000, True, 'not a word'):
            with self.subTest(word=word):
                with self.assertRaises((ValueError, TypeError)):
                    self.inputs(next_word=word)

    def test_all_parent_return_aliases_and_corrupt_state_refused(self):
        sixth, *older = self.inputs()
        blocks, fields = sixth
        root = fields[0]
        for offset in range(0, 48, 4):
            candidate = (blocks, fields[:-1] + (root + offset,))
            with self.subTest(return_offset=offset):
                with self.assertRaises(ValueError):
                    inspect(candidate, *older)
        byte, regs, saved = older[-2]
        invalid = (
            (byte, tuple(regs[:-1]), saved),
            (byte, tuple(regs) + (('const', 0),), saved),
            (byte, tuple(regs), True),
            (byte, tuple(regs), -1),
            (byte, tuple(regs), 0x100000000),
        )
        for predecessor in invalid:
            mutated = list(older)
            mutated[-2] = predecessor
            with self.subTest(state=(len(predecessor[1]), predecessor[2])):
                with self.assertRaises((ValueError, TypeError, IndexError)):
                    inspect(sixth, *mutated)

    def test_branch_classification_never_calls_integer_decoder(self):
        branch = (16 << 26) | (12 << 21) | (2 << 16) | 16
        with patch(__name__ + '.classify',
                   side_effect=AssertionError('integer decoder invoked')) as decoder:
            result = inspect(*self.inputs(branch))
        self.assertEqual(result,
                         ('branch', 'not_integer', (0,) * 11,
                          0, 'not_attempted'))
        decoder.assert_not_called()

    def test_cli_fails_closed_without_private_inputs(self):
        script = Path(__file__).resolve()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            nonexistent = root / 'missing.dol'
            empty = root / 'empty.elf'
            empty.write_bytes(b'')
            for dol, elf, reason in (
                (nonexistent, nonexistent, 'private_input'),
                (empty, empty, 'size'),
            ):
                with self.subTest(reason=reason):
                    result = subprocess.run(
                        [sys.executable, str(script), str(dol), str(elf)],
                        capture_output=True, text=True, timeout=20,
                        check=False)
                    self.assertEqual(result.returncode, 1)
                    self.assertEqual(result.stdout.strip(),
                                     'FORMATTER_128_PROVENANCE '
                                     'verified=0 reason=' + reason)
                    self.assertEqual(result.stderr, '')

    def test_plan_passes_fully_authenticated_predecessors(self):
        sixth, fifth, fourth, third, second, signext, immediate, copy, predecessor, compare = (
            self.inputs())
        names = ('byte_plan', 'compare_plan', 'copy_plan', 'immediate_plan',
                 'signext_plan', 'second_plan', 'third_plan',
                 'fourth_plan', 'fifth_plan', 'sixth_plan')
        values = (predecessor, compare, copy, immediate, signext,
                  second, third, fourth, fifth, sixth)
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
        'size', 'next sixth immediate contract',
        'next sixth immediate provenance', 'next sixth immediate state',
    }
    try:
        if (q.dol is None or q.elf is None or
                not 256 <= q.dol.stat().st_size <= MAX_DOL or
                not 52 <= q.elf.stat().st_size <= 64 * 1024 * 1024):
            raise ValueError('size')
        with plan_cache_scope():
            (family, name, counts, modeled, reason), branch = plan(
                q.dol.read_bytes(), q.elf.read_bytes(), with_branch=True)
    except (OSError, ValueError, TypeError, KeyError, IndexError,
            struct.error) as error:
        msg = str(error)
        print('FORMATTER_128_PROVENANCE verified=0 reason=' +
              (msg.replace(' ', '_') if msg in safe else 'private_input'))
        return 1
    reads, writes, constant, stack, partial, other, cr, carry, xer, oe, alias = counts
    branch_report = ''
    if branch is not None:
        form, reads_cr, decrements_ctr, links, absolute, target = branch
        branch_report = (f'branch_form={form} cr_read={reads_cr} '
                         f'ctr_decrement={decrements_ctr} link={links} '
                         f'absolute={absolute} target_class={target} ')
    print(
        f'FORMATTER_128_PROVENANCE verified=1 previous_127_fixture=1 '
        f'next_original_word=1 family={family} operation={name} '
        f'reads={reads} writes={writes} constant_inputs={constant} '
        f'stack_inputs={stack} partial_inputs={partial} '
        f'other_inputs={other} condition_write={cr} carry_read={carry} '
        f'xer_write={xer} overflow_enable={oe} alias={alias} '
        f'gpr_model={modeled} reason={reason.replace(" ", "_")} '
        f'{branch_report}original_execution=0'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
