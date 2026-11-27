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

    def test_saved_nonvolatile_destination_is_not_valid_for_copy_120(self):
        # The generic integer planner permits some saved registers, but the
        # exact 120th original word must keep the volatile-only contract.
        # Neither the private fixture nor the generated header may widen it.
        self.mask = (1 << 16)
        with self.assertRaisesRegex(ValueError, 'report copy encoding'):
            self.contract(word=or_copy(dst=16))
        valid, fields = self.contract(word=or_copy(dst=10))
        self.assertEqual(fields[6], 10)
        # Keep the encoded destination and the contract field consistent
        # so the rendered-header rejection is specifically about register class.
        nonvolatile = list(fields)
        nonvolatile[2] = or_copy(dst=16)
        nonvolatile[6] = 16
        with self.assertRaisesRegex(ValueError, 'report copy rendering'):
            render((valid, tuple(nonvolatile)))

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

    def test_shared_native_harness_preprocessor_scope(self):
        # The harness is shared by dozens of older modes. Merely compiling
        # witness headers cannot catch a missing #endif in this translation
        # unit, nor a mode accidentally nested under an unrelated option.
        from re import match
        path = Path(__file__).with_name('test_native_scheduler_postack_v1256.cpp')
        scopes = []
        seen = set()
        for number, line in enumerate(path.read_text().splitlines(), 1):
            directive = match(r'^\s*#\s*(if|ifdef|ifndef|elif|else|endif)\b(.*)', line)
            if directive:
                kind, expression = directive.groups()
                if kind in ('if', 'ifdef', 'ifndef'):
                    scopes.append((number, expression.strip()))
                elif kind == 'endif':
                    self.assertTrue(scopes, f'unmatched endif at {number}')
                    scopes.pop()
                else:
                    self.assertTrue(scopes, f'unmatched {kind} at {number}')
            if 'int main(int argc,char** argv)' in line:
                self.assertEqual(scopes, [], 'main must be unconditional')
                seen.add('main')
            if 'if(formatter_nested->stage()==16u)' in line:
                self.assertNotIn('UNDERCOVER_FORMATTER_CALLER_MIXED',
                                 [value for _, value in scopes])
                seen.add('post-integer')
            if 'if(formatter_nested->stage()==28u)' in line:
                values = [value for _, value in scopes]
                self.assertEqual(values.count('UNDERCOVER_FORMATTER_CALLER_NEXT_ENTRY'), 1)
                self.assertNotIn('UNDERCOVER_FORMATTER_CALLER_REPORT_BYTE', values)
                seen.add('next-entry')
            if 'if(formatter_nested->stage()==30u)' in line:
                values = [value for _, value in scopes]
                self.assertEqual(values.count('UNDERCOVER_FORMATTER_CALLER_NEXT_ENTRY'), 1)
                self.assertEqual(values.count('UNDERCOVER_FORMATTER_CALLER_REPORT_BYTE'), 1)
                self.assertNotIn('UNDERCOVER_FORMATTER_CALLER_REPORT_COMPARE', values)
                seen.add('byte')
        self.assertEqual(scopes, [], 'unterminated native harness conditionals')
        self.assertEqual(seen, {'main', 'post-integer', 'next-entry', 'byte'})

    def test_native_120_call_chain_keeps_three_guarded_words(self):
        # The first owner attempt reached native compilation before failing
        # on an extended witness overload. Catch missing copy arguments in
        # the shared harness during original-free checks instead.
        import re
        source = Path(__file__).with_name(
            'test_native_scheduler_postack_v1256.cpp').read_text()
        calls = (
            ('!formatter_nested->resume_caller_next_entry(',
             'return;'),
            ('!formatter_report_byte->arm_native(',
             'return;'),
            ('!formatter_report_compare->arm(',
             'return;'),
        )
        expected = (r'#ifdef UNDERCOVER_FORMATTER_CALLER_REPORT_COPY'
                    r'\s*,formatter_report_copy_private::next_word\s*#endif')
        for opening, terminal in calls:
            with self.subTest(call=opening):
                self.assertEqual(source.count(opening), 1)
                fragment = source.split(opening, 1)[1].split(terminal, 1)[0]
                self.assertRegex(fragment, expected)
                self.assertEqual(
                    fragment.count('formatter_report_copy_private::next_word'), 1)
        self.assertIn(
            'c.mmu.write32(formatter_report_copy_private::next_pc+4u,0x44000002u);',
            source)

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
