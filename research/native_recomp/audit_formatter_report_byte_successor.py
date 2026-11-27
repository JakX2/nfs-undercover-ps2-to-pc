#!/usr/bin/env python3
"""Read-only operand/provenance census of the original callee's post-byte integer.

This script neither translates nor executes the proprietary instruction.
Its only public output is bounded opcode family and operand-kind counts.
"""
import argparse
import struct
import unittest
from unittest.mock import patch
from collections import Counter
from pathlib import Path

from audit_formatter_partial_copy import boundary_shape
from audit_formatter_partial_integer import classify
from guarded_continuation import GUARD
from prepare_formatter_caller_integer_contract import step
from private_plan_cache import plan_cache_scope
from prepare_v419_full_start import MAX_DOL

_ALLOWED_REASONS = {
    'caller integer effects',
    'caller integer opcode',
    'caller integer encoding',
    'caller integer inputs',
    'caller integer registers',
}


def inspect(contract, registers, *, saved_mask=0, return_input=False):
    """Classify a proven byte load's successor, without inventing registers."""
    blocks, info = contract
    if len(info) != 8 or len(registers) != 32:
        raise ValueError('successor state')
    root, load, _, _, value, next_pc, integer, _ = info
    op, rt, xo = load >> 26, (load >> 21) & 31, (load >> 1) & 1023
    if (root & 3 or next_pc != root + 4 or
            not (op == 34 or op == 31 and xo == 87 and not load & 1) or
            rt not in (0, *range(3, 13)) or
            type(value) is not int or not 0 <= value <= 255 or
            type(saved_mask) is not int or saved_mask < 0 or saved_mask > 0xffffffff or
            blocks.get(root) != (load, integer, GUARD) or
            boundary_shape(integer) != 'integer'):
        raise ValueError('successor boundary')
    if not all(isinstance(v, tuple) and len(v) == 2 and
               isinstance(v[0], str) for v in registers):
        raise ValueError('successor state')
    if registers[1][0] != 'stack':
        raise ValueError('successor frame')
    after = list(registers)
    after[rt] = ('const', value)  # proven zero-extension, no read or execution
    name, reads, writes, cr, carry, xer, overflow = classify(integer)
    input_kinds = Counter(after[r][0] for r in set(reads))
    counts = (
        len(set(reads)), len(set(writes)),
        input_kinds['const'], input_kinds['stack'],
        input_kinds['partial'],
        len(set(reads)) - input_kinds['const'] - input_kinds['stack'] -
        input_kinds['partial'],
        cr, carry, xer, overflow,
        int(bool(set(reads) & set(writes))),
    )
    reason = 'supported'
    try:
        modeled, _ = step(integer, tuple(after), saved_mask=saved_mask)
    except ValueError as ex:
        modeled = None
        reason = str(ex) if str(ex) in _ALLOWED_REASONS else 'not_modelled'
    result = (name, counts, modeled, reason)
    if not return_input:
        return result
    # Return only a previously authenticated symbolic constant. The byte
    # destination is not necessarily the compare source register.
    if name != 'compare_immediate' or reason != 'supported' or modeled is None or len(set(reads)) != 1:
        raise ValueError('successor compare source')
    source = next(iter(reads))
    tag = after[source]
    if (tag[0] != 'const' or type(tag[1]) is not int or
            not 0 <= tag[1] <= 0xffffffff):
        raise ValueError('successor compare source')
    return (*result, (source, tag[1]))


def plan(d, e, *, return_input=False, include_byte=False):
    from prepare_formatter_next_entry_report_byte_contract import plan as byte_plan

    # Reuse the already validated 118 contract's original caller GPR state.
    # No second full caller/ancestor re-analysis of the same boundary.
    byte, registers, mask = byte_plan(d, e, with_live=True)
    if byte[0].get(byte[1][0]) != (byte[1][1], byte[1][6], GUARD):
        raise ValueError('successor history')
    result = inspect(byte, registers, saved_mask=mask, return_input=return_input)
    return (byte, result) if include_byte else result


class Tests(unittest.TestCase):
    def setUp(self):
        self.root = 0x80010000
        self.load = (34 << 26) | (9 << 21) | (7 << 16) | 1
        self.integer = (14 << 26) | (10 << 21) | (9 << 16) | 1
        self.regs = [('reg', i) for i in range(32)]
        self.regs[1] = ('stack', -864)
        self.value = 0x5a

    def contract(self):
        return ({self.root: (self.load, self.integer, GUARD)},
                (self.root,self.load,753,17,self.value,
                 self.root+4,self.integer,self.root+0x100))

    def probe(self, *, mask=0):
        return inspect(self.contract(), tuple(self.regs), saved_mask=mask)

    def test_constant_byte_source(self):
        name, counts, modeled, reason = self.probe()
        self.assertEqual((name, reason), ('add_immediate','supported'))
        self.assertEqual(counts[:4], (1,1,1,0))
        self.assertEqual(modeled[10], ('const', 0x5b))
        self.assertEqual(self.regs[9], ('reg',9))

    def test_all_byte_values_and_wrap(self):
        for v in range(256):
            self.value = v
            self.assertEqual(self.probe()[2][10], ('const',v+1))
        self.value = 255
        self.integer = (14<<26)|(10<<21)|(9<<16)|0xffff
        self.assertEqual(self.probe()[2][10], ('const',254))

    def test_or_immediate(self):
        self.integer = (24<<26)|(9<<21)|(10<<16)|0x0100
        self.assertEqual(self.probe()[2][10], ('const',0x15a))

    def test_compare_needs_condition_witness(self):
        self.integer = (11<<26)|(0<<23)|(0<<21)|(9<<16)|0x5a
        name, counts, modeled, reason = self.probe()
        self.assertEqual(name,'compare_immediate')
        self.assertEqual(counts[6],1)
        self.assertEqual(reason,'supported')
        self.assertEqual(modeled[9], ('const',0x5a))
        details = inspect(self.contract(), tuple(self.regs), return_input=True)
        self.assertEqual(details[-1], (9, 0x5a))

    def test_different_constant_register_is_authenticated(self):
        self.integer = (10<<26)|(4<<23)|(7<<16)|0x8000
        self.regs[7] = ('const', 0x81234567)
        details = inspect(self.contract(), tuple(self.regs), return_input=True)
        self.assertEqual(details[0], 'compare_immediate')
        self.assertEqual(details[3], 'supported')
        self.assertEqual(details[-1], (7, 0x81234567))
        self.assertNotEqual(details[-1][0], (self.load>>21)&31)
        self.assertEqual(self.regs[9], ('reg',9))

    def test_unproven_comparison_input_refused(self):
        self.integer = (11<<26)|(3<<23)|(7<<16)|0
        with self.assertRaisesRegex(ValueError, 'successor compare source'):
            inspect(self.contract(), tuple(self.regs), return_input=True)
        self.integer = (14<<26)|(10<<21)|(9<<16)|1
        with self.assertRaisesRegex(ValueError, 'successor compare source'):
            inspect(self.contract(), tuple(self.regs), return_input=True)

    def test_plan_reuses_single_authenticated_snapshot(self):
        self.integer=(10<<26)|(4<<23)|(7<<16)|0x8000
        self.regs[7]=('const',0x81234567)
        expected=self.contract()
        with patch('prepare_formatter_next_entry_report_byte_contract.plan',
                   return_value=(expected,tuple(self.regs),0)) as owner:
            byte,details=plan(b'fixture',b'elf',return_input=True,include_byte=True)
        owner.assert_called_once_with(b'fixture',b'elf',with_live=True)
        self.assertEqual(byte,expected)
        self.assertEqual(details[0],'compare_immediate')
        self.assertEqual(details[-1],(7,0x81234567))

    def test_untracked_input_is_not_concretized(self):
        self.integer = (14<<26)|(10<<21)|(7<<16)|1
        name,counts,modeled,reason=self.probe()
        self.assertEqual(counts[5],1)
        self.assertIsNone(modeled)
        self.assertEqual(reason,'caller integer inputs')

    def test_nonvolatile_write_is_not_admitted(self):
        self.integer = (14<<26)|(15<<21)|(9<<16)|1
        self.assertIsNone(self.probe()[2])
        self.assertEqual(self.probe()[3],'caller integer effects')
        self.assertEqual(self.probe(mask=1<<15)[2][15], ('const',0x5b))

    def test_unmodeled_integer_is_reported_not_executed(self):
        self.integer=(31<<26)|(10<<21)|(9<<16)|(8<<11)|(459<<1)
        _,_,modeled,reason=self.probe()
        self.assertIsNone(modeled)
        self.assertEqual(reason,'caller integer opcode')

    def test_indexed_byte_load(self):
        self.load=(31<<26)|(9<<21)|(7<<16)|(8<<11)|(87<<1)
        self.assertEqual(self.probe()[2][10],('const',0x5b))

    def test_guards_and_provenance(self):
        self.value=True
        with self.assertRaisesRegex(ValueError,'boundary'):self.probe()
        self.value=0x5a
        self.integer=GUARD
        with self.assertRaisesRegex(ValueError,'boundary'):self.probe()
        self.integer=(14<<26)|(10<<21)|(9<<16)|1
        self.regs[1]=('reg',1)
        with self.assertRaisesRegex(ValueError,'frame'):self.probe()

    def test_invalid_load_or_state(self):
        self.load=(35<<26)|(9<<21)|(7<<16)|1
        with self.assertRaisesRegex(ValueError,'boundary'):self.probe()
        self.load=(34<<26)|(9<<21)|(7<<16)|1
        self.regs[9]=('computed',{})
        # The authenticated byte, never this unrelated predecessor, is read.
        self.assertEqual(self.probe()[2][10],('const',0x5b))


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('dol',type=Path,nargs='?')
    parser.add_argument('elf',type=Path,nargs='?')
    parser.add_argument('--self-test',action='store_true')
    q=parser.parse_args()
    if q.self_test:
        suite=unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
        return 0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1
    safe={'size','successor state','successor boundary','successor frame','successor history'}
    try:
        if (q.dol is None or q.elf is None or
            not 256<=q.dol.stat().st_size<=MAX_DOL or
            not 52<=q.elf.stat().st_size<=64*1024*1024):
            raise ValueError('size')
        with plan_cache_scope():
            name,counts,modeled,reason=plan(q.dol.read_bytes(),q.elf.read_bytes())
    except (OSError,ValueError,TypeError,KeyError,IndexError,struct.error) as ex:
        problem=str(ex)
        print('FORMATTER_REPORT_BYTE_SUCCESSOR verified=0 reason='+
              (problem.replace(' ','_') if problem in safe else 'private_input'))
        return 1
    reads,writes,const,stack,partial,other,cr,carry,xer,oe,alias=counts
    # Redacted aggregate-only output. This does not execute the 119th word.
    print(f'FORMATTER_REPORT_BYTE_SUCCESSOR verified=1 family={name} reads={reads} writes={writes} constant_inputs={const} stack_inputs={stack} partial_inputs={partial} other_inputs={other} condition_write={cr} carry_read={carry} xer_write={xer} overflow_enable={oe} alias={alias} gpr_model={int(modeled is not None)} reason={reason.replace(" ","_")} original_execution=0')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
