#!/usr/bin/env python3
"""Read-only, private provenance census of original instruction 120.

The original 119 native execution is a separately pinned prerequisite.
This audit authenticates the immediately following original instruction and
classifies its operand dependencies. It neither recompiles nor executes 120,
and never prints an original instruction word, address or GPR value.
"""
import argparse
import struct
import unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch

from audit_formatter_partial_copy import boundary_shape
from audit_formatter_partial_integer import classify
from guarded_continuation import GUARD
from prepare_formatter_caller_integer_contract import step
from prepare_formatter_report_compare_fixture import (
    plan as compare_plan, promote as promote_compare,
)
from prepare_v419_full_start import MAX_DOL
from private_plan_cache import plan_cache_scope

_ALLOWED_REASONS = frozenset({
    'caller integer effects', 'caller integer opcode',
    'caller integer encoding', 'caller integer inputs',
    'caller integer registers',
})


def inspect(compare_contract, predecessor):
    """Prove the two executed instructions before classifying the next word."""
    if (not isinstance(predecessor, tuple) or len(predecessor) != 3):
        raise ValueError('following predecessor')
    byte_contract, registers, mask = predecessor
    if (not isinstance(registers, (tuple,list)) or len(registers) != 32 or
            type(mask) is not int or mask < 0 or mask > 0xffffffff):
        raise ValueError('following state')
    byte_blocks, byte_info = byte_contract
    if len(byte_info) != 8:
        raise ValueError('following predecessor')
    root, load, _, _, value, label, comparison, ret = byte_info
    if (type(value) is not int or not 0 <= value <= 255 or
            label != root+4 or byte_blocks.get(root) != (load,comparison,GUARD)):
        raise ValueError('following predecessor')
    after = list(registers)
    if not all(isinstance(v,tuple) and len(v)==2 and isinstance(v[0],str)
               for v in after) or after[1][0]!='stack':
        raise ValueError('following state')
    rt=(load>>21)&31
    after[rt]=('const',value)
    after=tuple(after)
    if (not isinstance(compare_contract,tuple) or len(compare_contract)!=2 or
            len(compare_contract[1])!=7):
        raise ValueError('following contract')
    blocks,info=compare_contract
    croot,cmp,next_pc,next_word,src,constant,return_pc=info
    if (croot!=root or cmp!=comparison or next_pc!=root+8 or
            return_pc!=ret or type(next_word) is not int or
            not 0<=next_word<=0xffffffff or next_word==GUARD or
            src!=(comparison>>16)&31 or
            type(constant) is not int or not 0<=constant<=0xffffffff or
            blocks.get(root)!=(load,comparison,next_word,GUARD)):
        raise ValueError('following contract')
    if after[src]!=('const',constant):
        raise ValueError('following constant')
    try:
        gpr,inputs=step(comparison,after,saved_mask=mask)
    except ValueError:
        raise ValueError('following compare provenance') from None
    if gpr!=after or inputs!=((src,constant),):
        raise ValueError('following compare provenance')
    family=boundary_shape(next_word)
    # This is intentionally a classification, not a speculative guest step.
    if family!='integer':
        return family,'not_integer',(0,0,0,0,0,0,0,0,0,0,0),0,'not_attempted'
    name,reads,writes,cr,carry,xer,oe=classify(next_word)
    kinds=Counter(gpr[i][0] for i in set(reads))
    counts=(len(set(reads)),len(set(writes)),kinds['const'],
            kinds['stack'],kinds['partial'],
            len(set(reads))-kinds['const']-kinds['stack']-kinds['partial'],
            cr,carry,xer,oe,int(bool(set(reads)&set(writes))))
    try:
        modeled,_=step(next_word,gpr,saved_mask=mask)
        if len(modeled)!=32:
            raise ValueError('caller integer registers')
        reason='supported'
    except ValueError as ex:
        modeled=None
        reason=str(ex) if str(ex) in _ALLOWED_REASONS else 'not_modelled'
    return family,name,counts,int(modeled is not None),reason


def plan(dol,elf):
    from prepare_formatter_next_entry_report_byte_contract import plan as byte_plan
    predecessor=byte_plan(dol,elf,with_live=True)
    compare=compare_plan(dol,elf,predecessor=predecessor)
    return inspect(compare,predecessor)


class Tests(unittest.TestCase):
    def setUp(self):
        self.root=0x80010000
        self.load=(34<<26)|(9<<21)|(7<<16)|1
        self.comp=(11<<26)|(3<<23)|(7<<16)|0x8000
        self.word=(14<<26)|(10<<21)|(9<<16)|1
        self.regs=[('reg',i) for i in range(32)]
        self.regs[1]=('stack',-864)
        self.regs[7]=('const',0x81234567)
        self.byte=({self.root:(self.load,self.comp,GUARD)},
                   (self.root,self.load,753,17,0x5a,
                    self.root+4,self.comp,self.root+0x100))

    def probe(self,word=None,source=(7,0x81234567)):
        candidate=promote_compare(self.byte,self.word if word is None else word,source)
        return inspect(candidate,(self.byte,tuple(self.regs),0))

    def test_integer_full_width_source_preserved(self):
        family,name,counts,modeled,reason=self.probe()
        self.assertEqual((family,name,modeled,reason),
                         ('integer','add_immediate',1,'supported'))
        self.assertEqual(counts[:4],(1,1,1,0))
        self.assertEqual(self.regs[9],('reg',9))

    def test_all_byte_values_and_120_model(self):
        for byte in range(256):
            blocks,info=self.byte
            self.byte=(blocks,info[:4]+(byte,)+info[5:])
            self.assertEqual(self.probe()[3],1)

    def test_branch_is_visible_not_executed(self):
        word=(16<<26)|(12<<21)|(2<<16)|16
        family,name,counts,modeled,reason=self.probe(word)
        self.assertEqual((family,name,modeled,reason),
                         ('branch','not_integer',0,'not_attempted'))
        self.assertEqual(sum(counts),0)

    def test_untracked_integer_is_not_concretized(self):
        word=(14<<26)|(10<<21)|(6<<16)|1
        family,name,counts,modeled,reason=self.probe(word)
        self.assertEqual(family,'integer')
        self.assertEqual(counts[5],1)
        self.assertEqual((modeled,reason),(0,'caller integer inputs'))

    def test_corrupted_predecessor_refused(self):
        contract=promote_compare(self.byte,self.word,(7,0x81234567))
        wrong=list(self.regs);wrong[7]=('reg',7)
        with self.assertRaisesRegex(ValueError,'following constant'):
            inspect(contract,(self.byte,tuple(wrong),0))
        blocks,info=contract
        bad=({**blocks,self.root:(self.load,self.comp,self.word^1,GUARD)},info)
        with self.assertRaisesRegex(ValueError,'following contract'):
            inspect(bad,(self.byte,tuple(self.regs),0))
        with self.assertRaisesRegex(ValueError,'following predecessor'):
            inspect(contract,())
        with self.assertRaisesRegex(ValueError,'following state'):
            inspect(contract,(self.byte,tuple(self.regs[:31]),0))

    def test_one_shared_predecessor_snapshot(self):
        predecessor=(self.byte,tuple(self.regs),0)
        expected=promote_compare(self.byte,self.word,(7,0x81234567))
        with patch('prepare_formatter_next_entry_report_byte_contract.plan',
                   return_value=predecessor) as load, \
             patch('audit_formatter_report_compare_successor.compare_plan',
                   return_value=expected) as compare:
            result=plan(b'fixture',b'elf')
        load.assert_called_once_with(b'fixture',b'elf',with_live=True)
        compare.assert_called_once_with(b'fixture',b'elf',predecessor=predecessor)
        self.assertEqual(result[0],'integer')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('dol',type=Path,nargs='?')
    parser.add_argument('elf',type=Path,nargs='?')
    parser.add_argument('--self-test',action='store_true')
    q=parser.parse_args()
    if q.self_test:
        suite=unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
        return 0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1
    safe={'size','following predecessor','following state',
          'following contract','following constant','following compare provenance'}
    try:
        if (q.dol is None or q.elf is None or
            not 256<=q.dol.stat().st_size<=MAX_DOL or
            not 52<=q.elf.stat().st_size<=64*1024*1024):
            raise ValueError('size')
        with plan_cache_scope():
            family,name,counts,modeled,reason=plan(q.dol.read_bytes(),q.elf.read_bytes())
    except (OSError,ValueError,TypeError,KeyError,IndexError,struct.error) as error:
        msg=str(error)
        print('FORMATTER_120_SUCCESSOR verified=0 reason='+
              (msg.replace(' ','_') if msg in safe else 'private_input'))
        return 1
    reads,writes,constant,stack,partial,other,cr,carry,xer,oe,alias=counts
    print(f'FORMATTER_120_SUCCESSOR verified=1 previous_119=1 next_original_word=1 '
          f'family={family} operation={name} reads={reads} writes={writes} '
          f'constant_inputs={constant} stack_inputs={stack} partial_inputs={partial} '
          f'other_inputs={other} condition_write={cr} carry_read={carry} '
          f'xer_write={xer} overflow_enable={oe} alias={alias} gpr_model={modeled} '
          f'reason={reason.replace(" ","_")} original_execution=0')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
