#!/usr/bin/env python3
"""Read-only authenticated successor classification after original Wii 122.

Replays original byte-load, compare, stack copy, immediate and sign-ext
register state before classifying original instruction 123. No original
words, register values, addresses or translated code are printed.
This is never an instruction-123 native-execution claim.
"""
import argparse
import struct
import unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch

from audit_formatter_partial_copy import boundary_shape
from audit_formatter_partial_integer import classify
from audit_formatter_report_immediate_successor import Tests as AuditInputs
from prepare_formatter_caller_integer_contract import step
from prepare_formatter_next_entry_report_byte_contract import plan as byte_plan
from prepare_formatter_report_compare_fixture import plan as compare_plan
from prepare_formatter_report_stack_copy_fixture import plan as copy_plan
from prepare_formatter_report_immediate_fixture import plan as immediate_plan
from prepare_formatter_report_signext_fixture import (
    plan as signext_plan, promote as promote_signext,
)
from prepare_v419_full_start import MAX_DOL
from private_plan_cache import plan_cache_scope

_ALLOWED = frozenset({
    'caller integer opcode', 'caller integer encoding',
    'caller integer effects', 'caller integer inputs',
    'caller integer registers',
})


def inspect(signext, immediate, copy, predecessor, compare):
    if (not isinstance(signext, tuple) or len(signext) != 2 or
            not isinstance(signext[1], tuple) or len(signext[1]) != 9 or
            not isinstance(predecessor, tuple) or len(predecessor) != 3):
        raise ValueError('next signext contract')
    root, pc, word, next_pc, next_word, dst, before, value, ret = signext[1]
    if (type(next_word) is not int or
            not 0 <= next_word <= 0xffffffff):
        raise ValueError('next signext contract')
    try:
        expected = promote_signext(
            immediate, copy, predecessor, compare, next_word)
        if (signext != expected or pc != root + 16 or
                next_pc != root + 20 or ret != immediate[1][7]):
            raise ValueError('mismatch')
    except (ValueError, KeyError, IndexError, TypeError) as error:
        raise ValueError('next signext provenance') from error
    byte, regs, saved = predecessor
    if (not isinstance(regs, (tuple, list)) or len(regs) != 32 or
            type(saved) is not int or not 0 <= saved <= 0xffffffff):
        raise ValueError('next signext state')
    try:
        live = list(regs)
        load, byte_value = byte[1][1], byte[1][4]
        live[(load >> 21) & 31] = ('const', byte_value)
        after_compare, _ = step(byte[1][6], tuple(live), saved_mask=saved)
        after_copy, copy_inputs = step(
            copy[1][2], after_compare,
            saved_mask=saved, allow_stack_copy=True)
        after_121, immediate_inputs = step(
            immediate[1][2], after_copy, saved_mask=saved)
        after_122, signext_inputs = step(
            word, after_121, saved_mask=saved)
        if (copy_inputs or immediate_inputs or signext_inputs != ((dst,before),) or
                after_122[dst] != ('const', value) or
                after_122[1][0] != 'stack' or len(after_122) != 32):
            raise ValueError('state mismatch')
    except (ValueError, TypeError, IndexError, KeyError) as error:
        raise ValueError('next signext state') from error
    family = boundary_shape(next_word)
    if family != 'integer':
        return family, 'not_integer', (0,) * 11, 0, 'not_attempted'
    name, reads, writes, cr, carry, xer, oe = classify(next_word)
    read_set, write_set = set(reads), set(writes)
    kinds = Counter(after_122[i][0] for i in read_set)
    counts = (
        len(read_set), len(write_set), kinds['const'], kinds['stack'],
        kinds['partial'], len(read_set)-kinds['const']-kinds['stack']-kinds['partial'],
        cr, carry, xer, oe, int(bool(read_set & write_set)),
    )
    try:
        model, _ = step(next_word, after_122, saved_mask=saved,
                        allow_stack_copy=True, allow_stack_relative=True)
        if len(model) != 32:
            raise ValueError('caller integer registers')
        reason = 'supported'
    except ValueError as error:
        model = None
        reason = str(error) if str(error) in _ALLOWED else 'not_modelled'
    return family, name, counts, int(model is not None), reason


def plan(dol, elf):
    predecessor = byte_plan(dol, elf, with_live=True)
    compare = compare_plan(dol, elf, predecessor=predecessor)
    copy = copy_plan(dol, elf, predecessor=predecessor, compare=compare)
    immediate = immediate_plan(
        dol, elf, predecessor=predecessor, compare=compare, copy=copy)
    signext = signext_plan(
        dol, elf, predecessor=predecessor, compare=compare,
        copy=copy, immediate=immediate)
    return inspect(signext, immediate, copy, predecessor, compare)


class Tests(unittest.TestCase):
    def setUp(self):
        self.base = AuditInputs('test_constant_written_by_121_is_symbolic_input_to_122')
        self.base.setUp()

    @staticmethod
    def extsb(reg):
        return ((31 << 26) | (reg << 21) | (reg << 16) | (954 << 1))

    def contracts(self, word, reg=9):
        immediate, copy, predecessor, compare = self.base.inputs(self.extsb(reg))
        signext = promote_signext(
            immediate, copy, predecessor, compare, word)
        return signext, immediate, copy, predecessor, compare

    def test_constant_from_original_byte_load_is_preserved(self):
        word = (14 << 26) | (5 << 21) | (9 << 16) | 1
        family, name, counts, modeled, reason = inspect(*self.contracts(word))
        self.assertEqual((family, name, modeled, reason),
                         ('integer', 'add_immediate', 1, 'supported'))
        self.assertEqual(counts, (1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0))

    def test_signext_123_source_can_be_earlier_seed(self):
        word = (14 << 26) | (5 << 21) | (7 << 16) | 1
        result = inspect(*self.contracts(word, reg=7))
        self.assertEqual((result[0], result[1], result[2][2:6], result[3:]),
                         ('integer', 'add_immediate', (1, 0, 0, 0),
                          (1, 'supported')))

    def test_unknown_123_register_stays_unknown(self):
        word = (14 << 26) | (5 << 21) | (8 << 16) | 1
        result = inspect(*self.contracts(word))
        self.assertEqual((result[2][5], result[3], result[4]),
                         (1, 0, 'caller integer inputs'))

    def test_123_branch_classified_without_execution(self):
        word = (16 << 26) | (12 << 21) | (2 << 16) | 16
        self.assertEqual(inspect(*self.contracts(word)),
                         ('branch', 'not_integer', (0,) * 11, 0,
                          'not_attempted'))

    def test_sign_extension_before_123_is_symbolic(self):
        self.base.imm = (14 << 26) | (3 << 21) | 0xff80
        word = (14 << 26) | (5 << 21) | (3 << 16) | 1
        result = inspect(*self.contracts(word, reg=3))
        self.assertEqual((result[2][2], result[3], result[4]),
                         (1, 1, 'supported'))

    def test_tampered_signext_and_predecessor_fail(self):
        inputs = self.contracts((14 << 26) | (5 << 21) | (9 << 16) | 1)
        signext, immediate, copy, predecessor, compare = inputs
        root = self.base.root
        mutated = (
            ({**signext[0], root:signext[0][root][:-1] + (0,)}, signext[1]),
            (signext[0], signext[1][:7] + (0,) + signext[1][8:]),
            (signext[0], signext[1][:3] + (root+24,) + signext[1][4:]),
        )
        for alteration in mutated:
            with self.assertRaises(ValueError):
                inspect(alteration, immediate, copy, predecessor, compare)
        bad_reg = list(self.base.regs)
        bad_reg[7] = ('reg', 7)
        with self.assertRaises(ValueError):
            inspect(signext, immediate, copy,
                    (predecessor[0], tuple(bad_reg), 0), compare)

    def test_plan_reuses_authenticated_predecessors(self):
        inputs = self.contracts((14 << 26) | (5 << 21) | (9 << 16) | 1)
        signext, immediate, copy, predecessor, compare = inputs
        mocks = (
            patch(__name__ + '.byte_plan',return_value=predecessor),
            patch(__name__ + '.compare_plan',return_value=compare),
            patch(__name__ + '.copy_plan',return_value=copy),
            patch(__name__ + '.immediate_plan',return_value=immediate),
            patch(__name__ + '.signext_plan',return_value=signext),
        )
        with mocks[0] as b, mocks[1] as c, mocks[2] as d, \
             mocks[3] as e, mocks[4] as f:
            self.assertEqual(plan(b'dol', b'elf')[0], 'integer')
        b.assert_called_once_with(b'dol',b'elf',with_live=True)
        c.assert_called_once_with(b'dol',b'elf',predecessor=predecessor)
        d.assert_called_once_with(b'dol',b'elf',
                                  predecessor=predecessor,compare=compare)
        e.assert_called_once_with(b'dol',b'elf',
                                  predecessor=predecessor,compare=compare,
                                  copy=copy)
        f.assert_called_once_with(b'dol',b'elf',
                                  predecessor=predecessor,compare=compare,
                                  copy=copy,immediate=immediate)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('dol',type=Path,nargs='?')
    parser.add_argument('elf',type=Path,nargs='?')
    parser.add_argument('--self-test',action='store_true')
    q=parser.parse_args()
    if q.self_test:
        suite=unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
        return (0 if unittest.TextTestRunner(verbosity=2)
                .run(suite).wasSuccessful() else 1)
    safe={'size','next signext contract','next signext provenance',
          'next signext state'}
    try:
        if (q.dol is None or q.elf is None or
                not 256 <= q.dol.stat().st_size <= MAX_DOL or
                not 52 <= q.elf.stat().st_size <= 64 * 1024 * 1024):
            raise ValueError('size')
        with plan_cache_scope():
            family,name,counts,modeled,reason=plan(
                q.dol.read_bytes(),q.elf.read_bytes())
    except (OSError,ValueError,TypeError,KeyError,IndexError,
            struct.error) as error:
        msg=str(error)
        print('FORMATTER_123_PROVENANCE verified=0 reason='+
              (msg.replace(' ','_') if msg in safe else 'private_input'))
        return 1
    reads,writes,constant,stack,partial,other,cr,carry,xer,oe,alias=counts
    print(f'FORMATTER_123_PROVENANCE verified=1 previous_122_fixture=1 '
          f'next_original_word=1 family={family} operation={name} '
          f'reads={reads} writes={writes} constant_inputs={constant} '
          f'stack_inputs={stack} partial_inputs={partial} '
          f'other_inputs={other} condition_write={cr} carry_read={carry} '
          f'xer_write={xer} overflow_enable={oe} alias={alias} '
          f'gpr_model={modeled} reason={reason.replace(" ","_")} '
          f'original_execution=0')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
