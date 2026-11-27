#!/usr/bin/env python3
"""Admit one proven report-frame byte load; never execute or expose its value."""
import argparse
import struct
import unittest
from pathlib import Path
from guarded_continuation import GUARD, check_spans
from audit_formatter_partial_copy import boundary_shape
from prepare_formatter_partial_native_contract import read_address, read_value

def extend(entry, words, live, initial, inherited, current, report_size, classification):
    blocks, info = entry
    owner, size, call, call_word, target, w, ret = info
    if classification != ('report', 'constant', 'agrees'):
        raise ValueError('report byte provenance')
    if (owner == target or owner & 3 or target & 3 or call & 3 or
            not 8 <= size <= 65536 or size % 4 or
            not owner <= call < call + 4 < owner + size or ret != call + 4):
        raise ValueError('report byte geometry')
    body = blocks.get(owner, ())
    i = (call - owner) // 4
    if (i + 1 >= len(body) or body[i:i+2] != (call_word, GUARD) or
            blocks.get(target) != (w, GUARD) or
            len(words) != 3 or words[0] != w or words[1] == GUARD):
        raise ValueError('report byte history')
    op, rt, xo = w >> 26, (w >> 21) & 31, (w >> 1) & 1023
    if (not (op == 34 or (op == 31 and xo == 87 and not w & 1)) or
            rt not in (0, *range(3, 13))):
        raise ValueError('report byte opcode')
    if (len(live) != 32 or len(initial) != 32 or initial[1][0] != 'stack' or
            live[1] != initial[1] or not 8 <= report_size <= 512 or report_size % 8):
        raise ValueError('report byte state')
    site = read_address(w, live)
    if site is None or site[0] != 'stack' or site[2] != 1:
        raise ValueError('report byte address')
    _, at, _ = site
    parent_sp = initial[1][1]
    if not (parent_sp + 704 <= -report_size and -report_size + 8 <= at < 0):
        raise ValueError('report byte address')
    cell = current.get(at)
    if (cell is None or cell != inherited.get(at) or len(cell) != 2 or
            cell[0] != 'byte' or type(cell[1]) is not int or not 0 <= cell[1] <= 255):
        raise ValueError('report byte value')
    if read_value((cell,), w) != ('const', cell[1]):
        raise ValueError('report byte effect')
    expanded = {**blocks, target: (w, words[1], GUARD)}
    check_spans({a: 4 * len(ws) for a, ws in expanded.items()})
    return expanded, (target, w, at - parent_sp, at + report_size, cell[1],
                      target + 4, words[1], ret)

def plan(d, e, *, with_live=False):
    from prepare_formatter_caller_next_entry_contract import plan as entry_plan
    from audit_formatter_next_entry_ancestor_byte import plan as ancestor_plan
    from prepare_formatter_caller_stack_move_contract import plan as move_plan
    from audit_formatter_caller_after_stack_move import extend as integer_extend
    from prepare_formatter_continuation_plan import plan as continuation_plan
    from audit_formatter_partial_copy import plan as replay_plan
    from prepare_post_stm_sc_report import REPORT, report_trace
    from make_private_elf_symbol_map import parse_functions
    from make_v624_ipc_geometry import exact_words

    entry, load, relative, _ = entry_plan(d, e)
    _, info = entry
    if load[0] != 'outside_parent' or relative != 'above_parent' or load[1] != 1 or load[-2:] != ('volatile', 0):
        raise ValueError('report byte provenance')
    classification = ancestor_plan(d, e)
    move, live, cr, guards = move_plan(d, e)
    owner, size, *_ = move[1]
    saved_mask = continuation_plan(d, e)[6]
    contract, _, live, cr = integer_extend(move, exact_words(d, e, owner, size // 4),
                                          live, cr, saved_mask, guards)
    if contract[2:4] != info[2:4]:
        raise ValueError('report byte history')
    _, _, trace, _, replay_entry, _ = replay_plan(d, e, details=True)
    _, initial, inherited, _, _ = replay_entry
    _, _, _, current = trace[-1]
    sizes = parse_functions(e)
    target = info[4]
    if not 12 <= sizes.get(target, 0) <= 65536 or sizes[target] % 4:
        raise ValueError('report byte geometry')
    rw = exact_words(d, e, REPORT, sizes[REPORT] // 4)
    _, _, _, _, report_size, _ = report_trace(REPORT, rw)
    result = extend(entry, exact_words(d, e, target, 3), live, initial,
                    inherited, current, report_size, classification)
    return (result, tuple(live), saved_mask) if with_live else result

class Tests(unittest.TestCase):
    def setUp(self):
        self.p = 0x80010000
        self.t = self.p - 0x100
        self.call = self.p + 4
        self.bl = 0x48000001 | ((self.t - self.call) & 0x03fffffc)
        self.w = (34 << 26) | (9 << 21) | (7 << 16) | 1
        self.nop = 0x60000000
        self.blocks = {self.p: (GUARD, self.bl, GUARD), self.t: (self.w, GUARD)}
        self.live = [('reg', i) for i in range(32)]
        self.live[1] = ('stack', -864)
        self.live[7] = ('stack', -112)
        self.initial = tuple(self.live)
        self.inherited = {-111: ('byte', 0x5a)}
        self.current = dict(self.inherited)
        self.classification = ('report', 'constant', 'agrees')
        self.size = 128

    def probe(self, words=None):
        info = (self.p, 16, self.call, self.bl, self.t, self.w, self.call + 4)
        return extend((self.blocks, info), words or (self.w, self.nop, self.nop),
                      self.live, self.initial, self.inherited, self.current,
                      self.size, self.classification)

    def test_exact(self):
        blocks, info = self.probe()
        self.assertEqual(blocks, {**self.blocks, self.t: (self.w, self.nop, GUARD)})
        self.assertEqual(info, (self.t, self.w, 753, 17, 0x5a,
                               self.t + 4, self.nop, self.call + 4))

    def test_all_byte_values(self):
        for v in range(256):
            self.inherited[-111] = self.current[-111] = ('byte', v)
            self.assertEqual(self.probe()[1][4], v)

    def test_indexed(self):
        self.w = (31 << 26) | (9 << 21) | (7 << 16) | (8 << 11) | (87 << 1)
        self.blocks[self.t] = (self.w, GUARD)
        self.live[8] = ('const', 1)
        self.assertEqual(self.probe()[1][4], 0x5a)

    def test_unproven(self):
        for state in (('report','constant','missing'), ('helper','constant','agrees'),
                      ('report','register','agrees'), ('report','constant','conflict')):
            self.classification = state
            with self.assertRaisesRegex(ValueError, 'provenance'):
                self.probe()

    def test_guard(self):
        self.blocks[self.p] = (GUARD, self.bl, self.nop)
        with self.assertRaisesRegex(ValueError, 'history'):
            self.probe()

    def test_entry_guard(self):
        self.blocks[self.t] = (self.w, self.nop)
        with self.assertRaisesRegex(ValueError, 'history'):
            self.probe()

    def test_wrong_word(self):
        with self.assertRaisesRegex(ValueError, 'history'):
            self.probe((self.nop, self.nop, self.nop))

    def test_missing_successor(self):
        with self.assertRaisesRegex(ValueError, 'history'):
            self.probe((self.w, GUARD, self.nop))

    def test_wrong_opcode(self):
        for w in (self.w ^ (1 << 26), (self.w & ~(31 << 21)) | (14 << 21),
                  (self.w & ~(31 << 21)) | (1 << 21)):
            self.w = w
            self.blocks[self.t] = (w, GUARD)
            with self.assertRaisesRegex(ValueError, 'opcode'):
                self.probe()

    def test_wrong_stack(self):
        self.live[1] = ('stack', -856)
        with self.assertRaisesRegex(ValueError, 'state'):
            self.probe()

    def test_linkage(self):
        self.live[7] = ('stack', -128)
        with self.assertRaisesRegex(ValueError, 'address'):
            self.probe()

    def test_outside(self):
        self.live[7] = ('stack', 8)
        with self.assertRaisesRegex(ValueError, 'address'):
            self.probe()

    def test_changed(self):
        self.current[-111] = ('byte', 0x5b)
        with self.assertRaisesRegex(ValueError, 'value'):
            self.probe()

    def test_uninitialized(self):
        self.current[-111] = self.inherited[-111] = ('uninitialized', -111)
        with self.assertRaisesRegex(ValueError, 'value'):
            self.probe()

    def test_overlap(self):
        self.blocks[self.t + 8] = (GUARD,)
        with self.assertRaises(ValueError):
            self.probe()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('dol', type=Path, nargs='?')
    parser.add_argument('elf', type=Path, nargs='?')
    parser.add_argument('--self-test', action='store_true')
    q = parser.parse_args()
    if q.self_test:
        result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
        return 0 if result.wasSuccessful() else 1
    from prepare_v419_full_start import MAX_DOL
    from private_plan_cache import plan_cache_scope
    safe = {'size', 'report byte provenance', 'report byte geometry', 'report byte history',
            'report byte opcode', 'report byte state', 'report byte address',
            'report byte value', 'report byte effect'}
    try:
        if q.dol is None or q.elf is None or not 256 <= q.dol.stat().st_size <= MAX_DOL or not 52 <= q.elf.stat().st_size <= 64 * 1024 * 1024:
            raise ValueError('size')
        with plan_cache_scope():
            _, info = plan(q.dol.read_bytes(), q.elf.read_bytes())
    except (OSError, ValueError, TypeError, KeyError, IndexError, struct.error) as ex:
        print('FORMATTER_NEXT_ENTRY_REPORT_BYTE_CONTRACT verified=0 reason=' +
              (str(ex).replace(' ', '_') if str(ex) in safe else 'private_input'))
        return 1
    print('FORMATTER_NEXT_ENTRY_REPORT_BYTE_CONTRACT verified=1 admitted=1 width=1 source=report replay=agrees volatile=1 update=0 next_guard=1 caller_return_guard=1 next_family=' +
          boundary_shape(info[-2]) + ' original_execution=0')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
