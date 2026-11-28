#!/usr/bin/env python3
"""Private read-only expansion of the selected 128 target for one cmpi.

Only the selected target's existing guard may be replaced. The new
successor is an unexecuted observation label; its successor remains a
guard. No new root, original instruction dump, or native execution.
"""
import argparse
import struct
import unittest
from pathlib import Path
from unittest.mock import patch

from audit_formatter_branch_128_target_successor import compare_source
from guarded_continuation import GUARD, check_spans
from make_v624_ipc_geometry import exact_words
from prepare_formatter_branch_128_fixture import plan as branch_plan, render as render_branch
from prepare_formatter_next_entry_report_byte_contract import plan as byte_plan
from prepare_v419_full_start import MAX_DOL
from private_plan_cache import plan_cache_scope


def promote(branch, predecessor, words):
    render_branch(branch)
    blocks, fields = branch
    owner, _, _, target, comparison, unused, taken, extent, ret = fields
    if (taken != 1 or target == unused or
            blocks.get(target) != (comparison, GUARD) or
            comparison >> 26 != 11 or comparison & 0x00600000 or
            target + 12 > owner + extent or
            not isinstance(words, (tuple, list)) or len(words) != 2 or
            any(type(w) is not int or not 0 <= w <= 0xffffffff for w in words) or
            words[0] != comparison or words[1] == GUARD or
            target <= ret < target + 12):
        raise ValueError('compare 129 geometry')
    kind, source = compare_source(branch, predecessor)
    if kind != 'constant' or source is None:
        raise ValueError('compare 129 source')
    reg, value = source
    if (type(reg) is not int or reg != (comparison >> 16) & 31 or
            type(value) is not int or not 0 <= value <= 0xffffffff):
        raise ValueError('compare 129 source')
    expanded = {**blocks, target: (comparison, words[1], GUARD)}
    check_spans({address: 4 * len(body) for address, body in expanded.items()})
    return expanded, (target, comparison, target + 4, words[1], reg, value, ret)


def validate(branch, predecessor, words, candidate):
    """Independently verify every old root and every new private field."""
    if (not isinstance(candidate, tuple) or len(candidate) != 2 or
            not isinstance(candidate[0], dict) or
            not isinstance(candidate[1], tuple) or len(candidate[1]) != 7):
        raise ValueError('compare 129 contract')
    blocks, fields = candidate
    if any(type(x) is not int for x in fields):
        raise ValueError('compare 129 contract')
    target, comparison, following, word, reg, value, ret = fields
    if blocks.get(target) != (comparison, word, GUARD):
        raise ValueError('compare 129 contract')
    # Compare against a separately supplied DOL/ELF-verified pair, not
    # the candidate's own metadata (which could be forged together).
    expected = promote(branch, predecessor, words)
    if candidate != expected:
        raise ValueError('compare 129 contract')
    return fields


def render(branch, predecessor, words, candidate):
    target, comparison, following, word, reg, value, ret = validate(
        branch, predecessor, words, candidate)
    # Private owner workspace only. Never print this header in CI.
    return (
        'namespace formatter_compare_129_private {\n'
        f'inline constexpr uint32_t root=0x{target:08x}u,word=0x{comparison:08x}u;\n'
        f'inline constexpr uint32_t next_pc=0x{following:08x}u,next_word=0x{word:08x}u;\n'
        f'inline constexpr unsigned source_reg={reg}u;\n'
        f'inline constexpr uint32_t source_value=0x{value:08x}u,return_pc=0x{ret:08x}u;\n'
        '}\n')


def plan(dol, elf):
    branch = branch_plan(dol, elf)
    predecessor = byte_plan(dol, elf, with_live=True)
    target = branch[1][3]
    words = exact_words(dol, elf, target, 2)
    candidate = promote(branch, predecessor, words)
    validate(branch, predecessor, words, candidate)
    return branch, predecessor, words, candidate


class Tests(unittest.TestCase):
    def inputs(self, reg=6, eq=True):
        from audit_formatter_branch_128_target_successor import Tests as Base
        base = Base('test_compare_input_replayed_from_predecessor')
        comparison = (11 << 26) | (3 << 23) | (reg << 16) | 0xffff
        branch = base.fixture(comparison, eq=eq)
        predecessor = base.compare_predecessor(branch)
        return branch, predecessor, (comparison, 0x60000000)

    def test_exactly_one_existing_root_extended(self):
        branch, predecessor, words = self.inputs()
        candidate = promote(branch, predecessor, words)
        blocks, fields = candidate
        root = branch[1][3]
        self.assertEqual(set(blocks), set(branch[0]))
        self.assertEqual(blocks[root], (*words, GUARD))
        self.assertEqual(branch[0][root], (words[0], GUARD))
        self.assertEqual({a:w for a,w in blocks.items() if a != root},
                         {a:w for a,w in branch[0].items() if a != root})
        self.assertEqual(fields, (root, words[0], root+4, words[1],
                                  6, 5, branch[1][-1]))
        self.assertEqual(validate(branch, predecessor, words, candidate), fields)
        self.assertIn('source_value=0x00000005u',
                      render(branch, predecessor, words, candidate))

    def test_source_geometry_and_identity_refusals(self):
        branch, predecessor, words = self.inputs()
        for bad in ((words[0]^1, words[1]), (words[0], GUARD),
                    (words[0], -1), (words[0],), (*words, 0)):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                promote(branch, predecessor, bad)
        for reg in (1, 12):
            b, p, w = self.inputs(reg=reg)
            with self.assertRaisesRegex(ValueError, 'compare 129 source'):
                promote(b, p, w)
        b, p, w = self.inputs(eq=False)
        with self.assertRaises(ValueError):
            promote(b, p, w)
        # New guard must not reach outside original function extent.
        fields = branch[1]
        extent = fields[3] - fields[0] + 8
        edge = (branch[0], fields[:7]+(extent,)+fields[8:])
        with self.assertRaises(ValueError):
            promote(edge, predecessor, words)
        # Do not silently overwrite another already authenticated root.
        overlap = ({**branch[0], fields[3]+8:(GUARD,)}, fields)
        with self.assertRaises(ValueError):
            promote(overlap, predecessor, words)

    def test_render_refuses_changed_metadata_and_siblings(self):
        branch, predecessor, words = self.inputs()
        blocks, fields = promote(branch, predecessor, words)
        for slot in (0, 1, 2, 4, 5, 6):
            bad = fields[:slot]+(fields[slot]^1,)+fields[slot+1:]
            with self.subTest(slot=slot), self.assertRaises(ValueError):
                render(branch, predecessor, words, (blocks, bad))
        # Mutating the successor word and its corresponding field in
        # tandem must still fail against the separately authenticated pair.
        forged = dict(blocks)
        forged_word = words[1] ^ 1
        forged[fields[0]] = (words[0], forged_word, GUARD)
        forged_fields = fields[:3] + (forged_word,) + fields[4:]
        with self.assertRaises(ValueError):
            render(branch, predecessor, words, (forged, forged_fields))
        changed = dict(blocks)
        changed[branch[1][0]] = (GUARD,)
        with self.assertRaises(ValueError):
            render(branch, predecessor, words, (changed, fields))
        changed = dict(blocks)
        changed[fields[0]] = (*words, words[1])
        with self.assertRaises(ValueError):
            render(branch, predecessor, words, (changed, fields))

    def test_plan_authenticates_target_words_at_selected_pc(self):
        branch, predecessor, words = self.inputs()
        with patch(__name__+'.branch_plan', return_value=branch), \
             patch(__name__+'.byte_plan', return_value=predecessor), \
             patch(__name__+'.exact_words', return_value=words) as original:
            prior, state, authenticated, candidate = plan(b'dol', b'elf')
        original.assert_called_once_with(b'dol', b'elf', branch[1][3], 2)
        self.assertEqual(prior, branch)
        self.assertEqual(state, predecessor)
        self.assertEqual(authenticated, words)
        self.assertEqual(candidate, promote(branch, predecessor, words))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('dol', type=Path, nargs='?')
    parser.add_argument('elf', type=Path, nargs='?')
    parser.add_argument('--self-test', action='store_true')
    q = parser.parse_args()
    if q.self_test:
        return 0 if unittest.TextTestRunner(verbosity=2).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(Tests)).wasSuccessful() else 1
    try:
        if (q.dol is None or q.elf is None or
                not 256 <= q.dol.stat().st_size <= MAX_DOL or
                not 52 <= q.elf.stat().st_size <= 64 * 1024 * 1024):
            raise ValueError('size')
        with plan_cache_scope():
            branch, predecessor, words, candidate = plan(q.dol.read_bytes(), q.elf.read_bytes())
            render(branch, predecessor, words, candidate)
    except (OSError, ValueError, TypeError, KeyError, IndexError, struct.error):
        print('FORMATTER_129_COMPARE_FIXTURE verified=0')
        return 1
    print('FORMATTER_129_COMPARE_FIXTURE verified=1 previous_128_fixture=1 '
          'signed_immediate=1 constant_input=1 same_roots=1 selected_guard=1 '
          'successor_authenticated=1 original_execution=0')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
