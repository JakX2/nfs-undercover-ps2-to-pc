#!/usr/bin/env python3
"""Privately stage exactly one original forward-local 128 branch edge.

Requires independent provenance through instruction 127, a known original
119 compare-derived CR outcome, and a genuine forward-local branch target.
Never translates or executes the branch; never publishes game instructions,
private code addresses, or generated translated game code.
"""
import argparse
import struct
import unittest
from pathlib import Path
from unittest.mock import patch

from audit_formatter_branch_128_decision import inspect as inspect_decision
from audit_formatter_branch_128_geometry import geometry
from guarded_continuation import GUARD, check_spans
from make_private_elf_symbol_map import parse_functions
from make_v624_ipc_geometry import exact_words
from prepare_formatter_next_entry_report_byte_contract import plan as byte_plan
from prepare_formatter_report_compare_fixture import plan as compare_plan
from prepare_formatter_report_sixth_immediate_fixture import plan as sixth_plan
from prepare_v419_full_start import MAX_DOL
from private_plan_cache import plan_cache_scope


def promote(sixth, compare, words, extent):
    """Replace only the unexecuted branch edge with a private stop guard."""
    if (not isinstance(sixth, tuple) or len(sixth) != 2 or
            not isinstance(sixth[0], dict) or
            not isinstance(sixth[1], tuple) or len(sixth[1]) != 8 or
            not isinstance(words, (tuple, list)) or
            not all(type(w) is int and 0 <= w <= 0xffffffff for w in words) or
            type(extent) is not int or extent & 3 or
            not 52 <= extent <= 65536):
        raise ValueError('branch fixture shape')
    root, pc127, instruction127, pc128, branch, _, _, ret = sixth[1]
    blocks = sixth[0]
    prior = blocks.get(root)
    if (not isinstance(prior, tuple) or len(prior) != 12 or
            prior[-1] != GUARD or prior[9:11] !=
            (instruction127, branch) or
            pc127 != root + 36 or pc128 != root + 40 or
            root & 3 or not 0x80000000 <= root < 0x81800000 or
            root + extent > 0x81800000 or
            root <= ret < root + extent or
            ret & 3 or len(words) > extent // 4 or
            tuple(words[:11]) != prior[:11]):
        raise ValueError('branch fixture predecessor')
    source, taken, provenance = inspect_decision(sixth, compare)
    if (source, provenance) != ('original_compare', 'known'):
        raise ValueError('branch fixture outcome')
    form, relation, cr, ctr, lk, aa = geometry(
        branch, root, pc128, extent, ret)
    if (form, relation, cr, ctr, lk, aa) != (
            'conditional_direct', 'forward_local', 1, 0, 0, 0):
        raise ValueError('branch fixture target')
    delta = ((branch & 0xfffc) ^ 0x8000) - 0x8000
    target = pc128 + delta
    selected = target if taken else pc128 + 4
    unused = pc128 + 4 if taken else target
    if (target <= pc128 + 4 or selected == unused or
            target & 3 or selected & 3 or
            target + 4 >= root + extent or
            selected + 4 >= root + extent):
        raise ValueError('branch fixture guard')
    selected_index = (selected - root) // 4
    unused_index = (unused - root) // 4
    if max(selected_index, unused_index) >= len(words):
        raise ValueError('branch fixture words')
    selected_word = words[selected_index]
    if selected_word == GUARD:
        raise ValueError('branch fixture selected word')

    # Root is the first 11 authentic instructions (118..128). Guard any
    # path not taken. A forward selected target is a separate, bounded
    # two-word span. If the branch falls through, retain the original
    # fallthrough word and stop before it can enter the second label.
    out = dict(blocks)
    if taken:
        out[root] = tuple(words[:11]) + (GUARD,)
        out[selected] = (selected_word, GUARD)
    else:
        out[root] = tuple(words[:11]) + (selected_word, GUARD)
        # When target happens to equal the already guarded next label,
        # its stop guard must not be represented twice.
        if target != root + 48:
            out[target] = (GUARD,)
    try:
        check_spans({address: 4 * len(data) for address, data in out.items()})
    except (ValueError, KeyError, TypeError) as error:
        raise ValueError('branch fixture overlap') from error
    return (out, (root, pc128, branch, selected,
                  selected_word, unused, int(bool(taken)), extent, ret))


def render(fixture):
    """Owner-only C++ contract after the synthetic code spans are validated."""
    if (not isinstance(fixture, tuple) or len(fixture) != 2 or
            not isinstance(fixture[1], tuple) or len(fixture[1]) != 9):
        raise ValueError('branch fixture render')
    blocks, fields = fixture
    root, pc, branch, selected, word, unused, taken, extent, ret = fields
    if (not isinstance(blocks, dict) or
            any(type(v) is not int for v in fields) or
            taken not in (0, 1) or pc != root + 40 or
            selected & 3 or unused & 3 or
            root & 3 or not 0x80000000 <= root < 0x81800000 or
            root + extent > 0x81800000 or
            not 52 <= extent <= 65536 or extent & 3 or
            root <= ret < root + extent or
            blocks.get(root, ())[:11][-1:] != (branch,) or
            selected not in blocks and selected != root + 44):
        raise ValueError('branch fixture render')
    # Rendering is an independent trust boundary. A caller must not be
    # able to forge selected-edge metadata after private planning.
    root_span = blocks.get(root)
    if (not isinstance(root_span, tuple) or
            not all(type(x) is int and 0 <= x <= 0xffffffff
                    for x in root_span) or
            branch == GUARD or word == GUARD or
            selected == unused or
            selected == ret or unused == ret):
        raise ValueError('branch fixture render')
    try:
        shape = geometry(branch, root, pc, extent, ret)
        if shape != ('conditional_direct', 'forward_local', 1, 0, 0, 0):
            raise ValueError('branch fixture render')
        delta = ((branch & 0xfffc) ^ 0x8000) - 0x8000
        target = pc + delta
        if (target <= pc + 4 or
                target + 4 >= root + extent or
                selected + 4 >= root + extent or
                selected != (target if taken else pc + 4) or
                unused != (pc + 4 if taken else target)):
            raise ValueError('branch fixture render')
        if taken:
            if (len(root_span) != 12 or root_span[11] != GUARD or
                    blocks.get(selected) != (word, GUARD)):
                raise ValueError('branch fixture render')
        else:
            if (len(root_span) != 13 or
                    root_span[11:] != (word, GUARD) or
                    (target != root + 48 and
                     blocks.get(target) != (GUARD,))):
                raise ValueError('branch fixture render')
        check_spans({address: 4 * len(data)
                     for address, data in blocks.items()})
    except (ValueError, KeyError, TypeError) as error:
        raise ValueError('branch fixture render') from error
    # No details are exported by tests or CI. This string is generated
    # exclusively inside the private owner build workspace.
    return (
        'namespace formatter_branch_128_private {\n'
        f'inline constexpr uint32_t root=0x{root:08x}u,pc=0x{pc:08x}u,word=0x{branch:08x}u;\n'
        f'inline constexpr uint32_t selected_pc=0x{selected:08x}u,selected_word=0x{word:08x}u;\n'
        f'inline constexpr uint32_t return_pc=0x{ret:08x}u,owner_size={extent}u;\n'
        f'inline constexpr bool taken={str(bool(taken)).lower()};\n'
        '}\n')


def plan(dol, elf):
    predecessor = byte_plan(dol, elf, with_live=True)
    compare = compare_plan(dol, elf, predecessor=predecessor)
    sixth = sixth_plan(dol, elf, predecessor=predecessor, compare=compare)
    root = sixth[1][0]
    extent = parse_functions(elf).get(root, 0)
    if type(extent) is not int or extent & 3 or not 52 <= extent <= 65536:
        raise ValueError('branch fixture extent')
    instruction = sixth[1][4]
    delta = ((instruction & 0xfffc) ^ 0x8000) - 0x8000
    target = root + 40 + delta
    selected_index = (max(target, root + 44) - root) // 4
    if (target <= root + 44 or selected_index + 1 >= extent // 4):
        raise ValueError('branch fixture target')
    words = exact_words(dol, elf, root, selected_index + 2)
    return promote(sixth, compare, words, extent)


class Tests(unittest.TestCase):
    ROOT = 0x80010000
    RET = ROOT + 0x100

    def inputs(self, eq=True, disp=16):
        from audit_formatter_branch_128_decision import Tests as Base
        base = Base('test_equal_less_greater_and_inverted_cr_conditions')
        branch = base.bc(12, 6, disp)
        sixth, compare = base.inputs(branch=branch, known=7 if eq else 6)
        root = self.ROOT
        # The exact authentic prefix is compared against the sixth fixture.
        words = list(sixth[0][root][:11])
        words += [0x60000000] * 16
        return sixth, compare, tuple(words), 128

    def test_selected_and_untaken_edges_are_strictly_guarded(self):
        for eq in (False, True):
            with self.subTest(eq=eq):
                sixth, compare, words, extent = self.inputs(eq=eq)
                fixture = promote(sixth, compare, words, extent)
                blocks, fields = fixture
                selected = fields[3]
                unused = fields[5]
                self.assertEqual(fields[6], int(eq))
                self.assertEqual(blocks[selected][0]
                                 if eq else blocks[self.ROOT][11],
                                 words[(selected-self.ROOT)//4])
                if eq:
                    self.assertEqual(blocks[self.ROOT][11], GUARD)
                    self.assertEqual(blocks[selected][1], GUARD)
                else:
                    self.assertEqual(blocks[self.ROOT][12], GUARD)
                    self.assertEqual(blocks[unused], (GUARD,))
                self.assertIn('formatter_branch_128_private', render(fixture))

    def test_refuse_mutated_ancestor_alias_and_unsupported_target(self):
        sixth, compare, words, extent = self.inputs()
        bad = words[:4] + (words[4] ^ 1,) + words[5:]
        with self.assertRaises(ValueError):
            promote(sixth, compare, bad, extent)
        with self.assertRaises(ValueError):
            promote(sixth, compare, words, 44)
        with self.assertRaises(ValueError):
            promote(sixth, compare, words, True)
        with self.assertRaises(ValueError):
            promote(sixth, compare, words[:11], extent)
        with self.assertRaises(ValueError):
            promote(sixth, compare, words, 52)
        # A local branch is still not authorized if its CR bit is unknown.
        sixth2, compare2, words2, _ = self.inputs()
        fields = sixth2[1]
        branch = (16 << 26) | (12 << 21) | (2 << 16) | 16
        modified = ({**sixth2[0], self.ROOT:
                     sixth2[0][self.ROOT][:10] + (branch, GUARD)},
                    fields[:4] + (branch,) + fields[5:])
        altered_words = words2[:10] + (branch,) + words2[11:]
        with self.assertRaises(ValueError):
            promote(modified, compare2, altered_words, extent)

    def test_render_refuses_altered_edge_and_guard_metadata(self):
        for eq in (False, True):
            sixth, compare, words, extent = self.inputs(eq=eq)
            blocks, fields = promote(sixth, compare, words, extent)
            self.assertIn('formatter_branch_128_private',
                          render((blocks, fields)))
            for slot, replacement in (
                    (3, fields[3] + 4),  # selected label
                    (4, fields[4] ^ 1),  # selected original word
                    (5, fields[5] + 4),  # untaken label
                    (6, 1 - fields[6])):  # inverted decision
                modified = fields[:slot] + (replacement,) + fields[slot + 1:]
                with self.subTest(eq=eq, field=slot):
                    with self.assertRaises(ValueError):
                        render((blocks, modified))
            selected = fields[3]
            corrupted = dict(blocks)
            if eq:
                corrupted[selected] = (fields[4], 0x60000000)
            else:
                corrupted[self.ROOT] = (
                    corrupted[self.ROOT][:-1] + (0x60000000,))
            with self.assertRaises(ValueError):
                render((corrupted, fields))
            missing = dict(blocks)
            if eq:
                del missing[selected]
            else:
                del missing[fields[5]]
            with self.assertRaises(ValueError):
                render((missing, fields))

    def test_render_rejects_replayed_or_overlapping_spans(self):
        sixth, compare, words, extent = self.inputs()
        blocks, fields = promote(sixth, compare, words, extent)
        forged = dict(blocks)
        forged[fields[3] + 4] = (GUARD,)
        with self.assertRaises(ValueError):
            render((forged, fields))
        bad = fields[:4] + (GUARD,) + fields[5:]
        with self.assertRaises(ValueError):
            render((blocks, bad))

    def test_plan_requires_exact_owner_words(self):
        sixth, compare, words, extent = self.inputs()
        root = self.ROOT
        with patch(__name__ + '.byte_plan', return_value='byte') as byte_mock, \
             patch(__name__ + '.compare_plan', return_value=compare) as compare_mock, \
             patch(__name__ + '.sixth_plan', return_value=sixth) as sixth_mock, \
             patch(__name__ + '.parse_functions',
                   return_value={root: extent}) as functions, \
             patch(__name__ + '.exact_words', return_value=words[:16]) as original:
            fixture = plan(b'dol', b'elf')
        self.assertEqual(fixture[1][6], 1)
        byte_mock.assert_called_once_with(b'dol', b'elf', with_live=True)
        compare_mock.assert_called_once_with(b'dol', b'elf', predecessor='byte')
        sixth_mock.assert_called_once_with(b'dol', b'elf',
                                          predecessor='byte', compare=compare)
        functions.assert_called_once_with(b'elf')
        original.assert_called_once_with(b'dol', b'elf', root, 16)


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
        'size', 'branch fixture shape', 'branch fixture predecessor',
        'branch fixture outcome', 'branch fixture target', 'branch fixture guard',
        'branch fixture words', 'branch fixture selected word',
        'branch fixture overlap', 'branch fixture extent', 'branch fixture render',
    }
    try:
        if (q.dol is None or q.elf is None or
                not 256 <= q.dol.stat().st_size <= MAX_DOL or
                not 52 <= q.elf.stat().st_size <= 64 * 1024 * 1024):
            raise ValueError('size')
        with plan_cache_scope():
            fixture = plan(q.dol.read_bytes(), q.elf.read_bytes())
        render(fixture)
    except (OSError, ValueError, TypeError, KeyError, IndexError,
            struct.error) as error:
        msg = str(error)
        print('FORMATTER_128_BRANCH_FIXTURE verified=0 reason=' +
              (msg.replace(' ', '_') if msg in safe else 'private_input'))
        return 1
    print(
        'FORMATTER_128_BRANCH_FIXTURE verified=1 previous_127_fixture=1 '
        'original_branch=1 cr_outcome=1 selected_edge=1 opposite_guard=1 '
        'next_guard=1 original_execution=0'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
