#!/usr/bin/env python3
"""Source-only regression for the private original instruction 127 fixture."""
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from audit_formatter_report_fifth_immediate_successor import Tests as AuditInputs
from guarded_continuation import GUARD
from prepare_formatter_report_sixth_immediate_fixture import (
    EXPECTED_COUNTS, plan, promote, render,
)

FOLLOWING = 0x60000000


def addi(dst=5, base=0, imm=0xff80):
    return (14 << 26) | (dst << 21) | (base << 16) | (imm & 0xffff)


class SixthImmediateFixtureTests(unittest.TestCase):
    def setUp(self):
        self.base = AuditInputs(
            'test_instruction_126_constant_reaches_next_original_input')
        self.base.setUp()

    def contracts(self, word=None):
        return self.base.inputs(next_word=addi() if word is None else word)

    def test_exact_127_successor_guard_and_render(self):
        before = self.contracts()
        after = promote(*before, FOLLOWING)
        root = before[0][1][0]
        self.assertEqual(len(before[0][0][root]), 11)
        self.assertEqual(len(after[0][root]), 12)
        self.assertEqual(after[0][root][:-2], before[0][0][root][:-1])
        self.assertEqual(after[0][root][-2:], (FOLLOWING, GUARD))
        self.assertEqual(after[1],
                         (root, root + 36, addi(), root + 40,
                          FOLLOWING, 5, 0xffffff80, root + 0x100))
        self.assertEqual(EXPECTED_COUNTS,
                         (0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0))
        owner = render(after)
        self.assertIn('formatter_report_sixth_immediate_private', owner)
        self.assertIn('destination_reg=5u', owner)
        self.assertIn('value=0xffffff80u', owner)

    def test_signed_extremes_and_volatile_targets(self):
        for imm, value in ((0, 0), (1, 1), (0x7fff, 0x7fff),
                           (0x8000, 0xffff8000), (0xffff, 0xffffffff)):
            for dst in (0, 3, 5, 12):
                with self.subTest(imm=imm, dst=dst):
                    after = promote(*self.contracts(addi(dst, 0, imm)),
                                    FOLLOWING)
                    self.assertEqual(after[1][5:7], (dst, value))
                    render(after)

    def test_corrupted_successor_refused(self):
        before = self.contracts()
        for word in (GUARD, -1, 0x100000000, True, None, 'code'):
            with self.subTest(word=word):
                with self.assertRaises(ValueError):
                    promote(*before, word)

    def test_mutated_predecessor_and_return_alias_refused(self):
        original = self.contracts()
        fifth, *older = original
        blocks, fields = fifth
        root = fields[0]
        variants = (
            ({**blocks, root: blocks[root][:-1] + (0,)}, fields),
            (blocks, fields[:4] + (GUARD,) + fields[5:]),
            (blocks, fields[:6] + (0,) + fields[7:]),
            (blocks, fields[:-1] + (root + 44,)),
        )
        for candidate in variants:
            with self.subTest(fields=candidate[1]):
                with self.assertRaises(ValueError):
                    promote(candidate, *older, FOLLOWING)

    def test_render_refuses_modifications(self):
        after = promote(*self.contracts(), FOLLOWING)
        blocks, fields = after
        root = fields[0]
        variants = (
            ({**blocks, root: blocks[root][:-1] + (0,)}, fields),
            (blocks, fields[:4] + (GUARD,) + fields[5:]),
            (blocks, fields[:-1] + (root + 44,)),
        )
        for forged in variants:
            with self.subTest(forged=forged[1]):
                with self.assertRaises(ValueError):
                    render(forged)

    def test_plan_requires_exact_owner_words_and_extent(self):
        original = self.contracts()
        root = original[0][1][0]
        words = tuple(original[0][0][root][:10]) + (FOLLOWING,)
        kwargs = dict(
            predecessor=original[7], compare=original[8],
            copy=original[6], immediate=original[5],
            signext=original[4], second=original[3],
            third=original[2], fourth=original[1], fifth=original[0],
        )
        with patch('prepare_formatter_report_sixth_immediate_fixture.parse_functions',
                   return_value={root: 44}), \
             patch('prepare_formatter_report_sixth_immediate_fixture.exact_words',
                   return_value=words):
            self.assertEqual(plan(b'dol', b'elf', **kwargs)[1][4], FOLLOWING)
        for size in (0, 40, 45, 65540):
            with self.subTest(size=size):
                with patch('prepare_formatter_report_sixth_immediate_fixture.parse_functions',
                           return_value={root: size}):
                    with self.assertRaisesRegex(ValueError, 'extent'):
                        plan(b'dol', b'elf', **kwargs)
        bad = words[:6] + (0,) + words[7:]
        with patch('prepare_formatter_report_sixth_immediate_fixture.parse_functions',
                   return_value={root: 44}), \
             patch('prepare_formatter_report_sixth_immediate_fixture.exact_words',
                   return_value=bad):
            with self.assertRaisesRegex(ValueError, 'original'):
                plan(b'dol', b'elf', **kwargs)

    def test_generated_private_header_compiles(self):
        compiler = shutil.which('g++')
        if not compiler:
            self.skipTest('no g++ compiler')
        header = render(promote(*self.contracts(), FOLLOWING))
        code = '#include <cstdint>\n' + header + '''
using namespace formatter_report_sixth_immediate_private;
static_assert(pc==root+36u);
static_assert(next_pc==pc+4u);
static_assert(destination_reg==5u);
static_assert(value==0xffffff80u);
int main(){return 0;}
'''
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)/'sixth.cpp'
            p.write_text(code)
            result = subprocess.run(
                [compiler, '-std=c++20', '-Wall', '-Wextra', '-Werror',
                 '-fsyntax-only', str(p)],
                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main(verbosity=2)
