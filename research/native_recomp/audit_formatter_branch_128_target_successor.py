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
from prepare_formatter_next_entry_report_byte_contract import plan as byte_plan
from prepare_formatter_caller_integer_contract import step
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


# These are coarse architecture properties, not authorization to execute a
# memory instruction or evidence that its effective address is available.
_MEMORY_UPDATE_D = frozenset({33, 35, 37, 39, 41, 43, 45, 49, 51, 53, 55,
                              57, 61})
_MEMORY_UPDATE_X = frozenset({55, 119, 183, 247, 311, 375, 439, 567,
                              631, 695, 759})
_MEMORY_FAMILIES = frozenset({'load', 'store', 'floating_load',
                              'floating_store', 'paired_single_memory'})
# Opcode 4 uses a six-bit XW secondary opcode, not the ten-bit
# ordinary X-form field. The upper four bits encode W and GQR I.
_PSQ_INDEXED = frozenset({6, 7, 38, 39})
_PSQ_UPDATED = frozenset({38, 39})


def successor_family(word):
    if word >> 26 == 4 and ((word >> 1) & 63) in _PSQ_INDEXED:
        return 'paired_single_memory'
    return boundary_shape(word)


def memory_shape(word, family):
    if family not in _MEMORY_FAMILIES:
        return 'not_memory', 0, 1
    op = word >> 26
    if op == 4:
        mode = 'indexed'
        updated = int(((word >> 1) & 63) in _PSQ_UPDATED)
    elif op == 31:
        mode = 'indexed'
        updated = int(((word >> 1) & 1023) in _MEMORY_UPDATE_X)
    elif op in (46, 47):
        mode, updated = 'multiple', 0
    else:
        mode, updated = 'displacement', int(op in _MEMORY_UPDATE_D)
    ra, target = (word >> 16) & 31, (word >> 21) & 31
    # PowerPC forbids RA=0 for update forms, and RA=RT for GPR
    # load-update forms. An FP destination occupies a different register
    # bank and must not be rejected just because its index equals RA.
    valid = not updated or (ra != 0 and
                            (family != 'load' or ra != target))
    return mode, updated, int(valid)


def comparison_kind(word, family):
    # Signedness and operand form are sufficient to choose a future
    # native witness; never expose original operand indices or immediate.
    if family != 'integer':
        return 'not_integer'
    op = word >> 26
    if op == 10:
        return 'unsigned_immediate'
    if op == 11:
        return 'signed_immediate'
    if op == 31:
        xo = (word >> 1) & 1023
        if xo == 0:
            return 'signed_register'
        if xo == 32:
            return 'unsigned_register'
    return 'not_comparison'


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
    family = successor_family(original)
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
    memory_form, base_updated, update_base_valid = memory_shape(original, family)
    if not update_base_valid:
        raise ValueError('target successor invalid update base')
    return (family, reads, writes, cr, carry_read, xer, overflow, supported,
            branch_form, memory_form, base_updated, update_base_valid)


def compare_source(fixture, predecessor):
    """Classify a cmpi input using authenticated symbolic 118–127 state.

    The caller obtains both inputs from the owner-private planners.
    This is a read-only dependency check, not execution of instruction 129.
    The returned constant (when known) is for private fixture consumers only.
    """
    render(fixture)
    blocks, fields = fixture
    root, _, _, target, original, _, taken, _, ret = fields
    if taken != 1 or blocks.get(target) != (original, GUARD):
        raise ValueError('target compare provenance')
    if comparison_kind(original, successor_family(original)) != 'signed_immediate':
        return 'not_signed_immediate', None
    if original & 0x00600000:
        raise ValueError('target compare encoding')
    if (not isinstance(predecessor, tuple) or len(predecessor) != 3):
        raise ValueError('target compare state')
    byte, regs, saved = predecessor
    if (not isinstance(byte, tuple) or len(byte) != 2 or
            not isinstance(byte[0], dict) or
            not isinstance(byte[1], tuple) or len(byte[1]) != 8 or
            not isinstance(regs, (tuple, list)) or len(regs) != 32 or
            type(saved) is not int or not 0 <= saved <= 0xffffffff or
            saved & 0x3fff):
        raise ValueError('target compare state')
    b_root, load, _, _, value, label, comparison, b_ret = byte[1]
    body = blocks[root]
    if (b_root != root or b_ret != ret or label != root+4 or
            body[:2] != (load, comparison) or
            byte[0].get(root) != (load, comparison, GUARD) or
            type(value) is not int or not 0 <= value <= 255 or
            not all(isinstance(v, tuple) and len(v) == 2 and
                    isinstance(v[0], str) for v in regs) or
            regs[1][0] != 'stack'):
        raise ValueError('target compare provenance')
    # Replay only the authenticated predecessor effects. The taken bc
    # at slot 10 is CR-only and cannot change the comparison source.
    gp = list(regs)
    gp[(load >> 21) & 31] = ('const', value)
    live = tuple(gp)
    try:
        for index, word in enumerate(body[1:10], start=1):
            live, _ = step(word, live, saved_mask=saved,
                           allow_stack_copy=(index == 2))
    except (ValueError, KeyError, TypeError, IndexError):
        raise ValueError('target compare predecessor state') from None
    if len(live) != 32 or live[1] != regs[1]:
        raise ValueError('target compare predecessor state')
    reg = (original >> 16) & 31
    kind, value = live[reg]
    if kind != 'const':
        return (kind if kind in ('stack', 'partial', 'reg', 'lr')
                else 'untracked'), None
    if type(value) is not int or not 0 <= value <= 0xffffffff:
        raise ValueError('target compare source constant')
    try:
        after, inputs = step(original, live, saved_mask=saved)
    except ValueError:
        raise ValueError('target compare source constant') from None
    if after != live or inputs != ((reg, value),):
        raise ValueError('target compare source constant')
    return 'constant', (reg, value)


class Tests(unittest.TestCase):
    def fixture(self, selected_word=0x60000000, eq=True):
        from prepare_formatter_branch_128_fixture import Tests as Base, promote
        seed = Base('test_selected_and_untaken_edges_are_strictly_guarded')
        sixth, compare, words, size = seed.inputs(eq=eq)
        words = list(words)
        target = seed.ROOT + 40 + 16
        words[(target-seed.ROOT)//4] = selected_word
        return promote(sixth, compare, tuple(words), size)

    def compare_predecessor(self, fixture):
        root = fixture[1][0]
        body = fixture[0][root]
        byte = ({root: (body[0], body[1], GUARD)},
                (root, body[0], 753, 17, 0x5a, root+4,
                 body[1], fixture[1][-1]))
        regs = [('reg', i) for i in range(32)]
        regs[1] = ('stack', -864)
        regs[5] = ('const', 7)
        return byte, tuple(regs), 0

    def test_compare_input_replayed_from_predecessor(self):
        for reg, expected in ((6, ('constant', (6, 5))),
                              (7, ('constant', (7, 3))),
                              (0, ('constant', (0, 0x5a))),
                              (1, ('stack', None)),
                              (12, ('reg', None))):
            word = (11 << 26) | (3 << 23) | (reg << 16) | 0xffff
            fixture = self.fixture(word)
            before = self.compare_predecessor(fixture)
            self.assertEqual(compare_source(fixture, before), expected)
            self.assertEqual(before, self.compare_predecessor(fixture))

    def test_compare_input_refuses_invalid_predecessor(self):
        word = (11 << 26) | (6 << 16)
        fixture = self.fixture(word)
        byte, regs, saved = self.compare_predecessor(fixture)
        with self.assertRaises(ValueError):
            compare_source(fixture, (byte, regs[:31], saved))
        with self.assertRaises(ValueError):
            compare_source(fixture, (byte, regs, 1))
        with self.assertRaises(ValueError):
            compare_source(fixture, ((byte[0], byte[1][:-1] +
                                       (byte[1][-1] + 4,)), regs, saved))
        wrong = list(regs)
        wrong[5] = ('reg', 5)
        with self.assertRaises(ValueError):
            compare_source(fixture, (byte, tuple(wrong), saved))
        bad = self.fixture(word | 0x00200000)
        with self.assertRaises(ValueError):
            compare_source(bad, self.compare_predecessor(bad))
        self.assertEqual(compare_source(self.fixture(), None),
                         ('not_signed_immediate', None))

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

    def test_compare_discriminator_is_redacted_and_unambiguous(self):
        for op, kind in ((10, 'unsigned_immediate'), (11, 'signed_immediate')):
            for field in (0, 3, 7):
                for immediate in (0, 1, 0x7fff, 0x8000, 0xffff):
                    word = ((op << 26) | (field << 23) |
                            (5 << 16) | immediate)
                    with self.subTest(op=op, field=field):
                        self.assertEqual(comparison_kind(word, 'integer'), kind)
                        self.assertEqual(comparison_kind(
                            word, 'other'), 'not_integer')
        for xo, kind in ((0, 'signed_register'), (32, 'unsigned_register')):
            for ra, rb in ((3, 3), (3, 7), (0, 12)):
                word = ((31 << 26) | (ra << 16) | (rb << 11) |
                        (xo << 1))
                self.assertEqual(comparison_kind(word, 'integer'), kind)
        for word in (0x60000000, 0x44000002, 0):
            self.assertEqual(comparison_kind(word, 'integer'),
                             'not_comparison')

    def test_memory_addressing_modes_are_redacted_and_bounded(self):
        # No effective address, register ID or displacement is returned.
        cases = (
            (32 << 26, 'load', 'displacement', 0),  # lwz
            ((33 << 26) | (3 << 21) | (1 << 16),
             'load', 'displacement', 1),  # lwzu
            (46 << 26, 'load', 'multiple', 0),       # lmw
            (47 << 26, 'store', 'multiple', 0),      # stmw
            ((31 << 26) | (23 << 1), 'load', 'indexed', 0),
            ((31 << 26) | (3 << 21) | (1 << 16) | (55 << 1),
             'load', 'indexed', 1),
            ((31 << 26) | (151 << 1), 'store', 'indexed', 0),
            ((31 << 26) | (3 << 21) | (1 << 16) | (183 << 1),
             'store', 'indexed', 1),
            (48 << 26, 'floating_load', 'displacement', 0),
            ((49 << 26) | (1 << 21) | (1 << 16),
             'floating_load', 'displacement', 1),
            ((31 << 26) | (535 << 1), 'floating_load', 'indexed', 0),
            ((31 << 26) | (1 << 21) | (1 << 16) | (567 << 1),
             'floating_load', 'indexed', 1),
            (56 << 26, 'paired_single_memory', 'displacement', 0),
            ((57 << 26) | (2 << 21) | (1 << 16),
             'paired_single_memory', 'displacement', 1),
        )
        for word, family, mode, updated in cases:
            with self.subTest(family=family, mode=mode, updated=updated):
                actual = classify_target(self.fixture(word))
                self.assertEqual(actual[0], family)
                self.assertEqual(actual[9:], (mode, updated, 1))
                self.assertEqual(actual[1:8], (0, 0, 0, 0, 0, 0, 0))
        for word in (0x60000000, 0x48000010, 0x4e800020):
            actual = classify_target(self.fixture(word))
            self.assertEqual(actual[9:], ('not_memory', 0, 1))

    def test_paired_single_indexed_w_and_gqr_variants(self):
        # Four PPC750CL XW forms, with W and all eight GQR selectors.
        # The upper four bits must not be mistaken for an X-form opcode.
        for xo, updated in ((6, 0), (7, 0), (38, 1), (39, 1)):
            for w in (0, 1):
                for gqr in range(8):
                    word = ((4 << 26) | (2 << 21) | (5 << 16) |
                            (3 << 11) | (w << 10) | (gqr << 7) | (xo << 1))
                    with self.subTest(xo=xo, w=w, gqr=gqr):
                        result = classify_target(self.fixture(word))
                        self.assertEqual(result[0], 'paired_single_memory')
                        self.assertEqual(result[9:],
                                         ('indexed', updated, 1))
        # Nonmemory paired single operations retain the old classification.
        self.assertEqual(successor_family((4 << 26) | (21 << 1)),
                         'paired_single')
        for xo in (38, 39):
            illegal = (4 << 26) | (2 << 21) | (xo << 1)
            with self.subTest(xo=xo, invalid_base=True):
                self.assertEqual(memory_shape(illegal, 'paired_single_memory'),
                                 ('indexed', 1, 0))
                with self.assertRaisesRegex(ValueError, 'invalid update base'):
                    classify_target(self.fixture(illegal))

    def test_illegal_update_base_registers_are_rejected(self):
        # PowerPC update forms cannot use GPR0 as RA; integer load-update
        # also cannot overwrite its destination register as the base.
        cases = (
            (33 << 26, 'load'),
            ((33 << 26) | (3 << 21) | (3 << 16), 'load'),
            ((31 << 26) | (55 << 1), 'load'),
            ((31 << 26) | (3 << 21) | (3 << 16) | (55 << 1), 'load'),
            (37 << 26, 'store'),
            ((31 << 26) | (183 << 1), 'store'),
            (49 << 26, 'floating_load'),
            ((31 << 26) | (567 << 1), 'floating_load'),
            (57 << 26, 'paired_single_memory'),
        )
        for word, family in cases:
            with self.subTest(family=family, op=word >> 26):
                mode, updated, valid = memory_shape(word, family)
                self.assertIn(mode, ('displacement', 'indexed'))
                self.assertEqual((updated, valid), (1, 0))
                with self.assertRaisesRegex(ValueError, 'invalid update base'):
                    classify_target(self.fixture(word))

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
                (family, reads, writes, cr, carry_read, xer, overflow,
                 supported, form, memory_form, base_updated,
                 update_base_valid) = (
                    classify_target(self.fixture(word)))
                self.assertEqual(family, 'integer')
                self.assertEqual(
                    (reads, writes, cr, carry_read, xer, overflow, supported),
                    effects)
                self.assertEqual(form, 'not_branch')
                self.assertEqual((memory_form, base_updated),
                                 ('not_memory', 0))
                self.assertEqual(update_base_valid, 1)

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
                self.assertEqual(actual[9:], ('not_memory', 0, 1))

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
        self.assertEqual(result[9:], ('not_memory', 0, 1))

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
            dol, elf = q.dol.read_bytes(), q.elf.read_bytes()
            fixture = branch_plan(dol, elf)
            result = classify_target(fixture)
            comparison = comparison_kind(fixture[1][4], result[0])
            source_kind, source = compare_source(
                fixture, byte_plan(dol, elf, with_live=True)
                if comparison == 'signed_immediate' else None)
    except (OSError,ValueError,TypeError,KeyError,IndexError,
            struct.error) as error:
        safe = {'size','target successor provenance','target successor family',
                'target successor invalid update base', 'target compare provenance',
                'target compare encoding', 'target compare state',
                'target compare predecessor state', 'target compare source constant'}
        reason = str(error)
        print('FORMATTER_129_TARGET_AUDIT verified=0 reason=' +
              (reason.replace(' ','_') if reason in safe else 'private_input'))
        return 1
    (family, reads, writes, cr, carry_read, xer, overflow, supported,
     branch_form, memory_form, base_updated, update_base_valid) = result
    print(
        f'FORMATTER_129_TARGET_AUDIT verified=1 previous_128_fixture=1 '
        f'selected_edge=target family={family} reads={reads} writes={writes} '
        f'cr_write={cr} carry_read={carry_read} xer_write={xer} overflow_enable={overflow} '
        f'integer_classified={supported} branch_form={branch_form} '
        f'memory_form={memory_form} base_updated={base_updated} '
        f'update_base_valid={update_base_valid} comparison_kind={comparison} '
        f'compare_source={source_kind} constant_input={int(source is not None)} '
        'original_execution=0'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
