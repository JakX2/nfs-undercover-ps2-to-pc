#!/usr/bin/env python3
"""Read-only proof of the CR decision at original formatter branch 128.

The owner must authenticate the complete 118-127 predecessor, its original
119 compare source and all intervening non-record instructions. No original
word, PC, register contents or branch destination may appear in public logs.
No branch is executed or emulated.
"""
import argparse
import struct
import unittest
from pathlib import Path
from unittest.mock import patch

from audit_formatter_report_sixth_immediate_successor import branch_shape
from guarded_continuation import GUARD
from prepare_formatter_next_entry_report_byte_contract import plan as byte_plan
from prepare_formatter_report_compare_fixture import plan as compare_plan
from prepare_formatter_report_sixth_immediate_fixture import plan as sixth_plan
from prepare_v419_full_start import MAX_DOL
from private_plan_cache import plan_cache_scope


def inspect(sixth, compare):
    if (not isinstance(sixth, tuple) or len(sixth) != 2 or
            not isinstance(sixth[0], dict) or
            not isinstance(sixth[1], tuple) or len(sixth[1]) != 8 or
            not isinstance(compare, tuple) or len(compare) != 2 or
            not isinstance(compare[1], tuple) or len(compare[1]) != 7):
        raise ValueError('branch decision contract')
    root, pc, word, next_pc, branch, dst, value, ret = sixth[1]
    cmp_root, comparison, cmp_next, cmp_after, src, known, cmp_ret = compare[1]
    body = sixth[0].get(root)
    if (any(type(x) is not int for x in sixth[1]) or
            any(type(x) is not int for x in compare[1]) or
            not isinstance(body, tuple) or len(body) != 12 or
            root != cmp_root or ret != cmp_ret or
            pc != root + 36 or next_pc != root + 40 or
            cmp_next != root + 8 or
            src != ((comparison >> 16) & 31) or
            body[:4] != (body[0], comparison, cmp_after, body[3]) or
            body[1] != comparison or body[2] != cmp_after or
            body[9:] != (word, branch, GUARD)):
        raise ValueError('branch decision predecessor')
    # Authenticate all CR effects after the compare, not merely the
    # last immediate. 120 is non-record stack OR, 121 is li,
    # 122 is non-record extsb, 123-127 are zero-input addi.
    copy = body[2]
    signext = body[4]
    if (copy >> 26 != 31 or (copy >> 1) & 1023 != 444 or copy & 1 or
            body[3] >> 26 != 14 or
            signext >> 26 != 31 or (signext >> 1) & 1023 != 954 or
            signext & 1 or
            any(x >> 26 != 14 for x in body[5:10])):
        raise ValueError('branch decision preserved cr')
    family, cr_read, ctr_dec, linked, absolute, _ = branch_shape(branch)
    if (family, cr_read, ctr_dec, linked, absolute) != (
            'conditional_direct', 1, 0, 0, 0):
        return 'unsupported_branch', 0, 'not_attempted'
    if (comparison >> 26 not in (10, 11) or
            comparison & 0x00600000 or not 0 <= known <= 0xffffffff):
        raise ValueError('branch decision comparison')
    bf = (comparison >> 23) & 7
    bi = (branch >> 16) & 31
    if bi >> 2 != bf or bi & 3 == 3:
        # Without the original incoming CR bit/SO provenance, the branch
        # outcome remains unknown. Do not copy a live arbitrary CR bit.
        return 'unknown_cr', 0, 'not_attempted'
    imm = comparison & 0xffff
    if comparison >> 26 == 10:
        lt = known < imm
    else:
        signed = known if known < 0x80000000 else known - 0x100000000
        imm_signed = imm if imm < 0x8000 else imm - 0x10000
        lt = signed < imm_signed
    eq = known == (imm if comparison >> 26 == 10
                   else imm_signed & 0xffffffff)
    bit = (lt, not lt and not eq, eq)[bi & 3]
    taken = bit == bool(branch & 0x01000000)  # BO[3] toggles expected CR value
    return 'original_compare', int(taken), 'known'


def plan(dol, elf):
    predecessor = byte_plan(dol, elf, with_live=True)
    compare = compare_plan(dol, elf, predecessor=predecessor)
    sixth = sixth_plan(dol, elf, predecessor=predecessor, compare=compare)
    return inspect(sixth, compare)


class Tests(unittest.TestCase):
    ROOT = 0x80010000
    RET = ROOT + 0x100

    @staticmethod
    def cmpwi(op=11, bf=1, ra=5, imm=7):
        return (op << 26) | (bf << 23) | (ra << 16) | (imm & 0xffff)

    @staticmethod
    def bc(bo=12, bi=6, disp=16):
        return (16 << 26) | (bo << 21) | (bi << 16) | (disp & 0xfffc)

    def inputs(self, comparison=None, branch=None, known=7):
        root = self.ROOT
        compare_word = (self.cmpwi() if comparison is None else comparison)
        branch_word = self.bc() if branch is None else branch
        body = (
            (34 << 26), compare_word,
            (31 << 26) | (5 << 21) | (6 << 16) | (5 << 11) | (444 << 1),
            (14 << 26) | (7 << 21) | 3,
            (31 << 26) | (7 << 21) | (7 << 16) | (954 << 1),
            (14 << 26) | (3 << 21) | 1,
            (14 << 26) | (4 << 21) | 2,
            (14 << 26) | (8 << 21) | 3,
            (14 << 26) | (9 << 21) | 4,
            (14 << 26) | (6 << 21) | 5,
            branch_word, GUARD)
        sixth = ({root: body}, (root, root+36, body[9], root+40,
                               branch_word, 6, 5, self.RET))
        compare = ({root: body[:3] + (GUARD,)},
                   (root, compare_word, root+8, body[2], 5, known, self.RET))
        return sixth, compare

    def test_equal_less_greater_and_inverted_cr_conditions(self):
        for known, flags in ((7, (0, 0, 1)), (6, (1, 0, 0)),
                             (8, (0, 1, 0))):
            for bit in (0, 1, 2):
                for bo in (4, 12):
                    branch = self.bc(bo, 4 + bit)
                    verdict = inspect(*self.inputs(branch=branch, known=known))
                    expected = int(bool(flags[bit]) == bool(bo & 8))
                    with self.subTest(value=known, bit=bit, bo=bo):
                        self.assertEqual(verdict,
                                         ('original_compare', expected, 'known'))

    def test_signed_and_unsigned_compare_extremes(self):
        cmp_signed = self.cmpwi(11, 1, 5, 0)
        cmp_unsigned = self.cmpwi(10, 1, 5, 0)
        self.assertEqual(inspect(*self.inputs(cmp_signed,
                         self.bc(12, 4), 0xffffffff))[1], 1)
        self.assertEqual(inspect(*self.inputs(cmp_unsigned,
                         self.bc(12, 4), 0xffffffff))[1], 0)

    def test_unknown_cr_and_unsupported_branch_stay_unresolved(self):
        self.assertEqual(inspect(*self.inputs(branch=self.bc(12, 2))),
                         ('unknown_cr', 0, 'not_attempted'))
        self.assertEqual(inspect(*self.inputs(branch=self.bc(12, 7))),
                         ('unknown_cr', 0, 'not_attempted'))
        self.assertEqual(inspect(*self.inputs(branch=0x48000010)),
                         ('unsupported_branch', 0, 'not_attempted'))
        self.assertEqual(inspect(*self.inputs(branch=self.bc(16, 6))),
                         ('unsupported_branch', 0, 'not_attempted'))

    def test_mutated_predecessor_and_cr_writers_refused(self):
        sixth, compare = self.inputs()
        blocks, fields = sixth
        for slot in (2, 3, 4, 5, 9):
            original = blocks[self.ROOT]
            bad = original[:slot] + (original[slot] | 1,) + original[slot+1:]
            with self.subTest(slot=slot):
                with self.assertRaises(ValueError):
                    inspect(({**blocks, self.ROOT: bad}, fields), compare)
        cmp_blocks, cmp_fields = compare
        for candidate in (
            (cmp_blocks, cmp_fields[:4] + (3,) + cmp_fields[5:]),
            (cmp_blocks, cmp_fields[:5] + (True,) + cmp_fields[6:]),
        ):
            with self.assertRaises(ValueError):
                inspect(sixth, candidate)

    def test_plan_reuses_authenticated_predecessors(self):
        sixth, compare = self.inputs()
        with patch(__name__ + '.byte_plan', return_value='byte') as byte_mock, \
             patch(__name__ + '.compare_plan', return_value=compare) as compare_mock, \
             patch(__name__ + '.sixth_plan', return_value=sixth) as sixth_mock:
            self.assertEqual(plan(b'dol', b'elf'),
                             ('original_compare', 1, 'known'))
        byte_mock.assert_called_once_with(b'dol', b'elf', with_live=True)
        compare_mock.assert_called_once_with(
            b'dol', b'elf', predecessor='byte')
        sixth_mock.assert_called_once_with(
            b'dol', b'elf', predecessor='byte', compare=compare)


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
    try:
        if (q.dol is None or q.elf is None or
                not 256 <= q.dol.stat().st_size <= MAX_DOL or
                not 52 <= q.elf.stat().st_size <= 64 * 1024 * 1024):
            raise ValueError('size')
        with plan_cache_scope():
            source, taken, provenance = plan(
                q.dol.read_bytes(), q.elf.read_bytes())
    except (OSError, ValueError, TypeError, KeyError, IndexError,
            struct.error) as error:
        safe = {'size', 'branch decision contract',
                'branch decision predecessor',
                'branch decision preserved cr',
                'branch decision comparison'}
        msg = str(error)
        print('FORMATTER_128_BRANCH_DECISION verified=0 reason=' +
              (msg.replace(' ', '_') if msg in safe else 'private_input'))
        return 1
    print(
        f'FORMATTER_128_BRANCH_DECISION verified=1 cr_source={source} '
        f'selected_edge={"target" if taken else "fallthrough" if provenance=="known" else "unknown"} '
        f'outcome_proven={int(provenance=="known")} '
        'original_execution=0'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
