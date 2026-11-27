#!/usr/bin/env python3
"""Read-only, owner-private geometry of original formatter branch 128.

Classifies the selected branch's *potential* target relation, never an
executed path, absolute address, displacement, word, or symbol name.
The original-127 fixture is authenticated before this inspection.
"""
import argparse
import struct
import unittest
from pathlib import Path

from audit_formatter_report_sixth_immediate_successor import branch_shape
from guarded_continuation import GUARD
from make_private_elf_symbol_map import parse_functions
from prepare_formatter_report_sixth_immediate_fixture import plan as sixth_plan
from prepare_v419_full_start import MAX_DOL
from private_plan_cache import plan_cache_scope


def geometry(word, root, pc, extent, return_pc):
    if (any(type(x) is not int for x in
            (word, root, pc, extent, return_pc)) or
            not 0 <= word <= 0xffffffff or word == GUARD or
            root & 3 or pc != root + 40 or
            not 0x80000000 <= root < 0x81800000 - 48 or
            extent & 3 or not 44 <= extent <= 65536 or
            return_pc & 3 or root <= return_pc < root + 48):
        raise ValueError('branch geometry')
    form, cr, ctr, linked, absolute, target_kind = branch_shape(word)
    if form.startswith('unsupported'):
        raise ValueError('branch form')
    if target_kind == 'lr':
        return form, 'link_register', cr, ctr, linked, absolute
    if target_kind == 'ctr':
        return form, 'count_register', cr, ctr, linked, absolute
    if target_kind != 'immediate':
        raise ValueError('branch target kind')
    op = word >> 26
    mask = 0xfffc if op == 16 else 0x03fffffc
    sign = 0x8000 if op == 16 else 0x02000000
    displacement = ((word & mask) ^ sign) - sign
    target = (displacement if absolute else pc + displacement) & 0xffffffff
    if target == return_pc:
        relation = 'return_alias'
    elif target == pc + 4:
        relation = 'fallthrough'
    elif target == pc:
        relation = 'self_loop'
    elif root <= target < root + extent:
        relation = 'backward_local' if target < pc else 'forward_local'
    else:
        relation = 'outside_function'
    return form, relation, cr, ctr, linked, absolute


def plan(dol, elf):
    sixth = sixth_plan(dol, elf)
    if (not isinstance(sixth, tuple) or len(sixth) != 2 or
            not isinstance(sixth[1], tuple) or len(sixth[1]) != 8):
        raise ValueError('branch predecessor')
    root, pc, _, next_pc, branch, _, _, ret = sixth[1]
    if next_pc != root + 40:
        raise ValueError('branch predecessor')
    extent = parse_functions(elf).get(root, 0)
    return geometry(branch, root, next_pc, extent, ret)


class Tests(unittest.TestCase):
    ROOT = 0x80010000
    PC = ROOT + 40
    RET = ROOT + 0x100

    @staticmethod
    def b(displacement, aa=0, lk=0):
        return (18 << 26) | (displacement & 0x03fffffc) | (aa << 1) | lk

    @staticmethod
    def bc(bo, bi, displacement):
        return ((16 << 26) | (bo << 21) | (bi << 16) |
                (displacement & 0xfffc))

    def classify(self, word, **kwargs):
        return geometry(word, kwargs.get('root', self.ROOT),
                        kwargs.get('pc', self.PC),
                        kwargs.get('extent', 128),
                        kwargs.get('return_pc', self.RET))

    def test_direct_and_conditional_target_relations(self):
        for word, relation in (
            (self.b(24), 'forward_local'),
            (self.b(-40), 'backward_local'),
            (self.b(0), 'self_loop'),
            (self.b(4), 'fallthrough'),
            (self.b(self.RET - self.PC), 'return_alias'),
            (self.b(0x200), 'outside_function'),
            (self.b(0x20, aa=1), 'outside_function'),
            (self.bc(12, 2, 24), 'forward_local'),
            (self.bc(4, 2, -40), 'backward_local'),
        ):
            with self.subTest(word=word):
                self.assertEqual(self.classify(word)[1], relation)

    def test_indirect_targets_stay_unresolved(self):
        for word, relation in (
            (0x4e800020, 'link_register'),
            (0x4e800420, 'count_register'),
        ):
            self.assertEqual(self.classify(word)[1], relation)

    def test_refuse_unsupported_and_untrusted_geometry(self):
        cases = (
            (GUARD, {}),
            (0x60000000, {}),
            ((19 << 26) | (16 << 21) | (528 << 1), {}),
            (self.b(4), {'pc': self.PC + 4}),
            (self.b(4), {'extent': 0}),
            (self.b(4), {'extent': 45}),
            (self.b(4), {'root': 0x81800000}),
            (self.b(4), {'return_pc': self.PC + 4}),
        )
        for word, args in cases:
            with self.subTest(word=word, args=args):
                with self.assertRaises(ValueError):
                    self.classify(word, **args)

    def test_plan_reuses_authenticated_sixth_fixture(self):
        word = self.bc(12, 2, 24)
        root = self.ROOT
        sixth = ({root: (0,) * 12},
                 (root, root + 36, 0, root + 40,
                  word, 7, 0, self.RET))
        from unittest.mock import patch
        with patch(__name__ + '.sixth_plan', return_value=sixth) as proof, \
             patch(__name__ + '.parse_functions',
                   return_value={root: 128}) as symbols:
            result = plan(b'dol', b'elf')
        self.assertEqual(result[1], 'forward_local')
        proof.assert_called_once_with(b'dol', b'elf')
        symbols.assert_called_once_with(b'elf')


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
            form, relation, cr, ctr, linked, absolute = plan(
                q.dol.read_bytes(), q.elf.read_bytes())
    except (OSError, ValueError, TypeError, KeyError, IndexError,
            struct.error) as error:
        safe = {'size', 'branch geometry', 'branch form',
                'branch target kind', 'branch predecessor'}
        msg = str(error)
        print('FORMATTER_128_BRANCH_GEOMETRY verified=0 reason=' +
              (msg.replace(' ', '_') if msg in safe else 'private_input'))
        return 1
    print(
        f'FORMATTER_128_BRANCH_GEOMETRY verified=1 previous_127_fixture=1 '
        f'form={form} target_relation={relation} cr_read={cr} '
        f'ctr_decrement={ctr} link={linked} absolute={absolute} '
        'target_execution=0 original_execution=0'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
