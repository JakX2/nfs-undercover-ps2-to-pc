#!/usr/bin/env python3
"""Identify the older live frame behind the next callee's byte load.

This is a census, not a read admission. No guest values are supplied,
no original code is run, and no private byte, offset or address is logged.
"""
import argparse
import struct
import unittest
from pathlib import Path


def classify(at, parent_sp, parent_size, report_size, helper_size,
             inherited, current, report_slots, helper_slots):
    if (parent_size != 704 or not 8 <= report_size <= 512 or report_size % 8
            or not 8 <= helper_size <= 256 or helper_size % 8
            or parent_sp + parent_size != -report_size - helper_size):
        raise ValueError('ancestor geometry')
    helper_sp = -report_size - helper_size
    report_sp = -report_size
    if at < helper_sp:
        raise ValueError('ancestor range')
    if at < report_sp:
        region, slots = 'helper', helper_slots
    elif at < 0:
        region, slots = 'report', report_slots
    else:
        return 'outer_or_older', 'not_audited', 'none'
    # The first word is the back chain and the second is a reserved
    # linkage word that can be changed by the immediately nested call.
    base = helper_sp if region == 'helper' else report_sp
    if base <= at < base + 8:
        return region, 'linkage', 'none'
    if any(not isinstance(a, int) or a % 4 for a in slots):
        raise ValueError('ancestor slot geometry')
    start = at & ~3
    source = slots.get(start)
    before, after = inherited.get(at), current.get(at)
    if before != after:
        return region, 'changed', 'none'
    if source is None:
        return region, 'not_modelled', 'none'
    kind, value = source
    if kind == 'const':
        if not isinstance(value, int) or not 0 <= value <= 0xffffffff:
            raise ValueError('ancestor constant')
        cell = ('byte', (value >> (24 - 8 * (at - start))) & 255)
    else:
        cell = ('part', source, 4, at - start)
    # The helper frame was not seeded by the earlier report-only model.
    # An independently modeled store is a candidate, not an observed byte.
    agreement = 'missing' if before is None else 'agrees' if before == cell else 'conflict'
    return region, ('constant' if kind == 'const' else
                    'stack_pointer' if kind == 'stack' else
                    'register' if kind == 'reg' else 'opaque'), agreement


def plan(d, e):
    from prepare_formatter_caller_next_entry_contract import plan as entry_plan
    from prepare_formatter_caller_stack_move_contract import plan as move_plan
    from audit_formatter_caller_after_stack_move import extend
    from prepare_formatter_continuation_plan import plan as continuation_plan
    from audit_formatter_partial_copy import plan as replay_plan
    from prepare_formatter_partial_native_contract import read_address
    from prepare_post_stm_sc_report import REPORT, report_trace
    from prepare_post_stm_sc_report_abi import model
    from prepare_post_stm_sc_report_helper_prefix import prefix
    from prepare_post_stm_sc_report_helper_fixture import plan as helper_plan
    from prepare_post_stm_sc_report_dependency_abi import compose
    from prepare_post_stm_sc_version import plan as version_plan
    from prepare_v419_full_start import EXPECTED_GPRS
    from make_private_elf_symbol_map import parse_functions
    from make_v624_ipc_geometry import exact_words

    (_, info), load, relative, _ = entry_plan(d, e)
    if load[0] != 'outside_parent' or relative != 'above_parent' or load[1] != 1 or load[-2:] != ('volatile', 0):
        raise ValueError('ancestor predecessor')
    move, live, cr, guards = move_plan(d, e)
    owner, size, *_ = move[1]
    contract, _, live, cr = extend(move, exact_words(d, e, owner, size // 4),
                                   live, cr, continuation_plan(d, e)[6], guards)
    if contract[2:4] != info[2:4]:
        raise ValueError('ancestor predecessor')
    address = read_address(info[-2], live)
    if address is None or address[0] != 'stack' or address[2] != 1:
        raise ValueError('ancestor load')
    _, at, _ = address
    _, _, trace, _, entry, _ = replay_plan(d, e, details=True)
    _, initial, inherited, _, _ = entry
    _, _, _, current = trace[-1]
    if live[1] != initial[1]:
        raise ValueError('ancestor geometry')
    sizes = parse_functions(e)
    rw = exact_words(d, e, REPORT, sizes[REPORT] // 4)
    _, _, _, _, report_size, helper = report_trace(REPORT, rw)
    if helper != helper_plan(d, e)[3][0]:
        raise ValueError('ancestor identity')
    report_regs, report_slots = model(REPORT, rw, details=True)
    _, _, _, fields = version_plan(d, e)
    regs = {2: EXPECTED_GPRS[2], 13: EXPECTED_GPRS[13],
            3: fields[5], 4: fields[4]}
    def substitute(v):
        return ('const', regs[v[1]]) if v[0] == 'reg' and v[1] in regs else v
    report_regs = tuple(substitute(v) for v in report_regs)
    report_slots = {a: substitute(v) for a, v in report_slots.items()}
    _, hs, helper_size, _ = prefix(helper, exact_words(d, e, helper, sizes[helper] // 4), details=True)
    helper_slots = {a - report_size: compose(v, report_regs, report_size) for a, v in hs.items()}
    return classify(at, live[1][1], 704, report_size, helper_size,
                    inherited, current, report_slots, helper_slots)


class Tests(unittest.TestCase):
    def probe(self, at, before=None, after=None, report=None, helper=None, sp=-864):
        return classify(at, sp, 704, 128, 32, before or {}, after or {},
                        report or {}, helper or {})
    def test_constant_byte_lanes_and_poisoning(self):
        # Exhaust the public big-endian byte extraction for every lane and
        # byte value. Matching symbolic reports alone never authorize a read.
        for lane in range(4):
            at = -112 + lane
            for value in range(256):
                word = value << (24 - 8 * lane)
                source = {-112: ('const', word)}
                matching = {at: ('byte', value)}
                poisoned = {at: ('byte', value ^ 0xff)}
                self.assertEqual(self.probe(at, matching, matching, source),
                                 ('report', 'constant', 'agrees'))
                self.assertEqual(self.probe(at, poisoned, poisoned, source),
                                 ('report', 'constant', 'conflict'))
                self.assertEqual(self.probe(at, matching, poisoned, source),
                                 ('report', 'changed', 'none'))

    def test_untracked_byte_cannot_gain_provenance(self):
        cell = {-112: ('byte', 0x7f)}
        self.assertEqual(self.probe(-112, cell, cell),
                         ('report', 'not_modelled', 'none'))

    def test_helper_and_report_boundary(self):
        self.assertEqual(self.probe(-152, helper={-152: ('const', 0x11223344)}),
                         ('helper', 'constant', 'missing'))
        self.assertEqual(self.probe(-120, report={-120: ('const', 0x11223344)}),
                         ('report', 'constant', 'missing'))
        for offset in (-160, -159, -156, -153, -128, -127, -124, -121):
            self.assertEqual(self.probe(offset)[1:], ('linkage', 'none'))

    def test_constant_agreement(self):
        for i in range(4):
            cell = {-112+i: ('byte', (0x12345678 >> (24-8*i)) & 255)}
            self.assertEqual(self.probe(-112+i, cell, cell, {-112: ('const', 0x12345678)}),
                             ('report', 'constant', 'agrees'))
    def test_constant_conflict(self):
        cell = {-112: ('byte', 0)}
        self.assertEqual(self.probe(-112, cell, cell, {-112: ('const', 0x12345678)}),
                         ('report', 'constant', 'conflict'))
    def test_helper_missing(self):
        self.assertEqual(self.probe(-148, helper={-148: ('const', 7)}),
                         ('helper', 'constant', 'missing'))
    def test_opaque_register(self):
        cell = {-110: ('part', ('reg', 4), 4, 2)}
        self.assertEqual(self.probe(-110, cell, cell, {-112: ('reg', 4)}),
                         ('report', 'register', 'agrees'))
    def test_pointer(self):
        self.assertEqual(self.probe(-112, report={-112: ('stack', 8)}),
                         ('report', 'stack_pointer', 'missing'))
    def test_changed(self):
        self.assertEqual(self.probe(-112, {-112: ('byte', 1)}, {-112: ('byte', 2)}),
                         ('report', 'changed', 'none'))
    def test_unmodelled(self):
        self.assertEqual(self.probe(-112), ('report', 'not_modelled', 'none'))
    def test_linkage(self):
        for a in (-160, -156, -128, -124):
            self.assertEqual(self.probe(a)[1:], ('linkage', 'none'))
    def test_older(self):
        self.assertEqual(self.probe(8), ('outer_or_older', 'not_audited', 'none'))
    def test_range(self):
        with self.assertRaisesRegex(ValueError, 'ancestor range'):
            self.probe(-161)
    def test_geometry(self):
        with self.assertRaisesRegex(ValueError, 'ancestor geometry'):
            self.probe(-112, sp=-856)
    def test_bad_slot(self):
        with self.assertRaisesRegex(ValueError, 'ancestor slot geometry'):
            self.probe(-112, report={-111: ('const', 1)})


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
    safe = {'ancestor geometry', 'ancestor predecessor', 'ancestor load',
            'ancestor identity', 'ancestor range', 'ancestor constant',
            'ancestor slot geometry', 'size'}
    try:
        if q.dol is None or q.elf is None or not 256 <= q.dol.stat().st_size <= MAX_DOL or not 52 <= q.elf.stat().st_size <= 64 * 1024 * 1024:
            raise ValueError('size')
        with plan_cache_scope():
            region, source, agreement = plan(q.dol.read_bytes(), q.elf.read_bytes())
    except (OSError, ValueError, TypeError, KeyError, IndexError, struct.error) as ex:
        print('FORMATTER_NEXT_ENTRY_ANCESTOR_BYTE verified=0 reason=' +
              (str(ex).replace(' ', '_') if str(ex) in safe else 'private_input'))
        return 1
    print(f'FORMATTER_NEXT_ENTRY_ANCESTOR_BYTE verified=1 region={region} source={source} replay={agreement} read_admitted=0 value_supplied=0 original_execution=0')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
