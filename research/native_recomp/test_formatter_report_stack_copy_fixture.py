#!/usr/bin/env python3
"""Original-free regressions for the authenticated 120 stack-copy fixture."""
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from guarded_continuation import GUARD
from prepare_formatter_report_compare_fixture import promote as promote_compare
from prepare_formatter_report_stack_copy_fixture import promote, render, plan

ROOT = 0x80010000
LOAD = (34 << 26) | (9 << 21) | (7 << 16) | 1
COMPARE = (11 << 26) | (3 << 23) | (7 << 16) | 0x8000
NEXT = (14 << 26) | (3 << 21) | (3 << 16) | 1
RETURN = ROOT + 0x100


def or_copy(src=1, dst=10, other=None, rc=0):
    if other is None:
        other = src
    return (31 << 26) | (src << 21) | (dst << 16) | (other << 11) | (444 << 1) | rc


class StackCopyFixture(unittest.TestCase):
    def setUp(self):
        self.byte = ({ROOT: (LOAD, COMPARE, GUARD)},
                     (ROOT, LOAD, 753, 17, 0x5a, ROOT+4, COMPARE, RETURN))
        self.registers = [('reg', i) for i in range(32)]
        self.registers[1] = ('stack', -864)
        self.registers[7] = ('const', 0x81234567)
        self.mask = 0

    def contract(self, word=None, offset=0, src=1, dst=10, next_word=NEXT):
        if word is None:
            word = or_copy(src, dst)
        if src != 1:
            self.registers[src] = ('stack', -864+offset)
        compare = promote_compare(self.byte, word, (7, 0x81234567))
        previous = (self.byte, tuple(self.registers), self.mask)
        return promote(compare, previous, next_word)

    def test_exact_guard_and_no_predecessor_modification(self):
        prior = dict(self.byte[0])
        out, fields = self.contract()
        self.assertEqual(self.byte[0], prior)
        self.assertEqual(out[ROOT], (LOAD,COMPARE,or_copy(),NEXT,GUARD))
        self.assertEqual(fields, (ROOT,ROOT+8,or_copy(),ROOT+12,NEXT,
                                  1,10,0,RETURN))
        self.assertIn('source_offset=0', render((out,fields)))
        self.assertIn('next_pc=', render((out,fields)))

    def test_negative_and_positive_stack_pointer_offsets(self):
        for offset in (-864,-48,-1,0,1,128,704,0x200000):
            with self.subTest(offset=offset):
                _,fields=self.contract(offset=offset,src=8,dst=4)
                self.assertEqual(fields[5:8],(8,4,offset))

    def test_noncopy_and_record_are_refused(self):
        for word in (or_copy(other=2), or_copy(rc=1),
                     or_copy(dst=1), or_copy(src=7), 0x60000000):
            with self.subTest(word=word):
                with self.assertRaises(ValueError):
                    self.contract(word=word)

    def test_range_and_untrusted_state_refusals(self):
        for offset in (-0x01800000, 0x01800000):
            with self.subTest(offset=offset):
                with self.assertRaisesRegex(ValueError, 'range'):
                    self.contract(offset=offset,src=8)
        for word in (GUARD, -1, 0x100000000, True, None):
            with self.subTest(word=word):
                with self.assertRaisesRegex(ValueError, 'successor'):
                    self.contract(next_word=word)
        self.registers[1] = ('reg',1)
        with self.assertRaises(ValueError):
            self.contract()

    def test_invalid_prior_and_original_size(self):
        candidate = promote_compare(self.byte,or_copy(),(7,0x81234567))
        with self.assertRaises(ValueError):
            promote(candidate, (self.byte,tuple(self.registers[:31]),self.mask), NEXT)
        prior=(self.byte,tuple(self.registers),self.mask)
        with patch('prepare_formatter_report_stack_copy_fixture.byte_plan',
                   return_value=prior), patch(
                   'prepare_formatter_report_stack_copy_fixture.compare_plan',
                   return_value=candidate), patch(
                   'prepare_formatter_report_stack_copy_fixture.parse_functions',
                   return_value={ROOT:20}), patch(
                   'prepare_formatter_report_stack_copy_fixture.exact_words',
                   return_value=(LOAD,COMPARE,or_copy(),NEXT)):
            out,_=plan(b'dol',b'elf')
        self.assertEqual(out[ROOT][-2:],(NEXT,GUARD))
        with patch('prepare_formatter_report_stack_copy_fixture.byte_plan',
                   return_value=prior), patch(
                   'prepare_formatter_report_stack_copy_fixture.compare_plan',
                   return_value=candidate), patch(
                   'prepare_formatter_report_stack_copy_fixture.parse_functions',
                   return_value={ROOT:16}):
            with self.assertRaisesRegex(ValueError, 'extent'):
                plan(b'dol',b'elf')

    def test_private_header_compiles(self):
        compiler=shutil.which('g++')
        if not compiler:
            self.skipTest('g++ unavailable')
        source='#include <cstdint>\n'+render(self.contract())+'''
using namespace formatter_report_copy_private;
static_assert(pc==root+8u);
static_assert(next_pc==pc+4u);
static_assert(source_reg==1u);
static_assert(destination_reg==10u);
static_assert(source_offset==0);
int main(){return 0;}
'''
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'stack_copy.cpp'
            p.write_text(source)
            run=subprocess.run([compiler,'-std=c++20','-Wall','-Wextra',
                                '-Werror','-fsyntax-only',str(p)],
                               capture_output=True,text=True,timeout=30)
            self.assertEqual(run.returncode,0,run.stderr)


if __name__ == '__main__':
    unittest.main(verbosity=2)
