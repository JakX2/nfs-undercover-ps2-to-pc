#!/usr/bin/env python3
"""Read-only, owner-private classification of the original 129th selected label.

This only inspects the first authenticated instruction at the original 128
taken branch destination. It does not interpret, translate or execute it.
No opcode, operand index, word, PC or target address is printed.
"""
import argparse
import struct
import unittest
from pathlib import Path

from audit_formatter_partial_copy import boundary_shape
from audit_formatter_partial_integer import classify
from audit_formatter_report_sixth_immediate_successor import branch_shape
from guarded_continuation import GUARD
from prepare_formatter_branch_128_fixture import plan as branch_plan, render
from prepare_v419_full_start import MAX_DOL
from private_plan_cache import plan_cache_scope


FAMILIES = frozenset({
    'integer', 'load', 'store', 'branch', 'direct', 'return',
    'system_control', 'floating_load', 'floating_store',
    'floating_arithmetic', 'paired_single', 'paired_single_memory',
    'condition_logical', 'condition_transfer', 'other',
})
BRANCH_FORMS = frozenset({
    'direct', 'conditional_direct', 'conditional_lr',
    'conditional_ctr', 'unsupported_ctr_branch', 'unsupported_branch',
    'not_branch',
})


def classify_target(fixture):
    # Revalidate the separately authenticated fixture at the boundary,
    # including target geometry, root membership and all code guards.
    render(fixture)
    blocks, fields = fixture
    root, pc, branch, target, original, unused, taken, size, ret = fields
    if (taken != 1 or target == unused or
            blocks.get(target) != (original, GUARD) or
            blocks.get(root, ())[-1:] != (GUARD,) or
            pc != root + 40 or size < 52 or branch == GUARD or
            original == GUARD):
        raise ValueError('target successor provenance')
    family = boundary_shape(original)
    if family not in FAMILIES:
        raise ValueError('target successor family')
    operation = 'not_integer'
    reads = writes = cr = carry_read = xer = overflow = supported = 0
    branch_form = 'not_branch'
    if family == 'integer':
        operation, read_regs, write_regs, cr, carry_read, xer, overflow = classify(original)
        # Exact reg indexes and raw immediate values stay owner-private.
        reads, writes = len(set(read_regs)), len(set(write_regs))
        supported = int(operation != 'unclassified')
        # Operation labels are not logged. Categorize by ability to use
        # the existing bounded integer observer, not by exact opcode.
    elif family in ('branch','direct','return','system_control'):
        branch_form = branch_shape(original)[0]
        if branch_form not in BRANCH_FORMS:
            branch_form = 'unsupported_branch'
    return family, reads, writes, cr, carry_read, xer, overflow, supported, branch_form


class Tests(unittest.TestCase):
    def fixture(self, selected_word=0x60000000, eq=True):
        from prepare_formatter_branch_128_fixture import Tests as Base, promote
        seed = Base('test_selected_and_untaken_edges_are_strictly_guarded')
        sixth, compare, words, size = seed.inputs(eq=eq)
        words = list(words)
        target = seed.ROOT + 40 + 16
        words[(target-seed.ROOT)//4] = selected_word
        return promote(sixth, compare, tuple(words), size)

    def test_integer_and_memory_classification(self):
        for word, family in (
            (0x60000000, 'integer'),
            ((14 << 26) | (3 << 21) | 1, 'integer'),
            ((32 << 26) | (3 << 21) | (1 << 16), 'load'),
            ((36 << 26) | (3 << 21) | (1 << 16), 'store'),
            (0x4e800020, 'return'),
            (0x48000010, 'branch'),
            ((16 << 26) | (12 << 21) | (2 << 16) | 16, 'branch'),
        ):
            with self.subTest(family=family,word=word):
                result = classify_target(self.fixture(word))
                self.assertEqual(result[0], family)
                self.assertIn(result[7], (0, 1))
                self.assertIn(result[8], BRANCH_FORMS)

    def test_integer_effect_metadata_matrix_is_bounded(self):
        # This is static classification of synthetic words. It must not
        # execute any branch or mutate an original native CPU snapshot.
        cases = (
            ((14 << 26) | (3 << 21) | 0x7fff,
             (0, 1, 0, 0, 0, 0, 1)),  # li r3,32767
            ((14 << 26) | (4 << 21) | (3 << 16) | 1,
             (1, 1, 0, 0, 0, 0, 1)),  # addi from r3
            ((11 << 26) | (1 << 23) | (3 << 16) | 2,
             (1, 0, 1, 0, 0, 0, 1)),  # cmpwi cr1,r3,2
            ((31 << 26) | (3 << 21) | (4 << 16) | (954 << 1),
             (1, 1, 0, 0, 0, 0, 1)),  # extsb
            ((31 << 26) | (3 << 21) | (1 << 16) | (467 << 1),
             (1, 0, 0, 0, 1, 0, 1)),  # mtspr xer,r3
            ((31 << 26) | (3 << 21) | (4 << 16) | (5 << 11) | (138 << 1),
             (2, 1, 0, 1, 1, 0, 1)),  # adde reads and updates XER.CA
        )
        for word, effects in cases:
            with self.subTest(word_family='integer', effects=effects):
                family, reads, writes, cr, carry_read, xer, overflow, supported, form = (
                    classify_target(self.fixture(word)))
                self.assertEqual(family, 'integer')
                self.assertEqual(
                    (reads, writes, cr, carry_read, xer, overflow, supported),
                    effects)
                self.assertEqual(form, 'not_branch')

    def test_control_transfers_never_claim_integer_observation(self):
        for word, family, form in (
            (0x4e800020, 'return', 'conditional_lr'),
            (0x48000010, 'branch', 'direct'),
            (0x48000011, 'direct', 'direct'),
            ((16 << 26) | (12 << 21) | (2 << 16) | 16,
             'branch', 'conditional_direct'),
        ):
            with self.subTest(family=family, form=form):
                actual = classify_target(self.fixture(word))
                self.assertEqual(actual[0], family)
                self.assertEqual(actual[1:8], (0, 0, 0, 0, 0, 0, 0))
                self.assertEqual(actual[8], form)

    def test_original_target_classification_never_retargets_128(self):
        original = self.fixture((14 << 26) | (3 << 21) | 0x7fff)
        before = (dict(original[0]), original[1])
        self.assertEqual(classify_target(original)[0], 'integer')
        self.assertEqual(original, before)
        blocks, fields = original
        tampered = dict(blocks)
        tampered[fields[3]] = (fields[4], 0x60000000)
        with self.assertRaises(ValueError):
            classify_target((tampered, fields))
        with self.assertRaises(ValueError):
            classify_target((blocks, fields[:4] + (0x44000002,) + fields[5:]))
        with self.assertRaises(ValueError):
            classify_target((blocks, fields[:6] + (0,) + fields[7:]))

    def test_unsupported_encodings_are_classification_not_execution(self):
        result = classify_target(self.fixture(0x00000000))
        self.assertEqual(result[0], 'other')
        self.assertEqual(result[7], 0)
        self.assertEqual(result[8], 'not_branch')

    def test_refuse_forged_target_and_untaken_sibling(self):
        with self.assertRaises(ValueError):
            classify_target(self.fixture(eq=False))
        blocks, fields = self.fixture()
        with self.assertRaises(ValueError):
            classify_target(({**blocks, fields[3]: (0x60000000, 0x60000000)},fields))
        with self.assertRaises(ValueError):
            classify_target((blocks, fields[:3]+(fields[3]+4,)+fields[4:]))
        with self.assertRaises(ValueError):
            classify_target((blocks, fields[:6]+(0,)+fields[7:]))

    def test_private_cli_does_not_log_untrusted_values(self):
        import inspect as pyinspect
        body = pyinspect.getsource(main)
        self.assertNotIn('{root}',body)
        self.assertNotIn('{branch}',body)
        self.assertNotIn('{target}',body)
        self.assertNotIn('{original}',body)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('dol', type=Path, nargs='?')
    parser.add_argument('elf', type=Path, nargs='?')
    parser.add_argument('--self-test', action='store_true')
    q = parser.parse_args()
    if q.self_test:
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
        return 0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1
    try:
        if (q.dol is None or q.elf is None or
                not 256 <= q.dol.stat().st_size <= MAX_DOL or
                not 52 <= q.elf.stat().st_size <= 64 * 1024 * 1024):
            raise ValueError('size')
        with plan_cache_scope():
            result = classify_target(branch_plan(q.dol.read_bytes(),
                                                 q.elf.read_bytes()))
    except (OSError,ValueError,TypeError,KeyError,IndexError,
            struct.error) as error:
        safe = {'size','target successor provenance','target successor family'}
        reason = str(error)
        print('FORMATTER_129_TARGET_AUDIT verified=0 reason=' +
              (reason.replace(' ','_') if reason in safe else 'private_input'))
        return 1
    family,reads,writes,cr,carry_read,xer,overflow,supported,branch_form = result
    print(
        f'FORMATTER_129_TARGET_AUDIT verified=1 previous_128_fixture=1 '
        f'selected_edge=target family={family} reads={reads} writes={writes} '
        f'cr_write={cr} carry_read={carry_read} xer_write={xer} overflow_enable={overflow} '
        f'integer_classified={supported} branch_form={branch_form} '
        'original_execution=0'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
