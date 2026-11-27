#!/usr/bin/env python3
"""Original-free regressions for the separately guarded original 121 contract."""
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from guarded_continuation import GUARD
from prepare_formatter_report_compare_fixture import promote as promote_compare
from prepare_formatter_report_stack_copy_fixture import promote as promote_copy
from prepare_formatter_report_immediate_fixture import promote, plan, render

ROOT = 0x80010000
LOAD = (34 << 26) | (9 << 21) | (7 << 16) | 1
COMPARE = (11 << 26) | (3 << 23) | (7 << 16) | 0x8000
COPY = (31 << 26) | (1 << 21) | (10 << 16) | (1 << 11) | (444 << 1)
RETURN = ROOT + 0x100
NEXT = 0x60000000


def addi(dst=3, base=0, imm=0xfffe, opcode=14):
    return ((opcode << 26) | (dst << 21) |
            (base << 16) | (imm & 0xffff))


class ReportImmediateFixture(unittest.TestCase):
    def setUp(self):
        self.byte = ({ROOT: (LOAD, COMPARE, GUARD)},
                     (ROOT, LOAD, 753, 17, 0x5a,
                      ROOT + 4, COMPARE, RETURN))
        self.gp = [('reg', i) for i in range(32)]
        self.gp[1] = ('stack', -864)
        self.gp[7] = ('const', 0x81234567)
        self.mask = 0

    def inputs(self, word=None, following=NEXT):
        if word is None:
            word = addi()
        predecessor = (self.byte, tuple(self.gp), self.mask)
        compare = promote_compare(self.byte, COPY, (7, 0x81234567))
        copy = promote_copy(compare, predecessor, word)
        return copy, predecessor, compare, following

    def test_exact_guard_move_and_value(self):
        old = self.inputs()
        copy, predecessor, compare, following = old
        contract = promote(*old)
        self.assertEqual(contract[0][ROOT],
                         (LOAD, COMPARE, COPY, addi(), NEXT, GUARD))
        self.assertEqual(contract[1], (ROOT, ROOT + 12, addi(),
                                       ROOT + 16, NEXT, 3,
                                       0xfffffffe, RETURN))
        self.assertEqual(copy[0][ROOT][-1], GUARD)
        self.assertEqual(copy[0][ROOT][-2], addi())
        self.assertEqual(self.byte[0][ROOT][-1], GUARD)
        text = render(contract)
        self.assertIn('destination_reg=3u', text)
        self.assertIn('value=0xfffffffeu', text)
        self.assertIn('next_pc=', text)

    def test_all_immediate_extremes_and_volatile_destinations(self):
        for imm, value in ((0, 0), (1, 1),
                           (0x7fff, 0x7fff),
                           (0x8000, 0xffff8000),
                           (0xffff, 0xffffffff)):
            for dst in (0, 3, 10, 12):
                with self.subTest(imm=imm, dst=dst):
                    contract = promote(*self.inputs(addi(dst=dst, imm=imm)))
                    self.assertEqual(contract[1][5:7], (dst, value))
                    render(contract)

    def test_provenance_and_nonvolatile_refusals(self):
        for word in (addi(dst=1), addi(dst=2), addi(dst=13),
                     addi(dst=14), addi(dst=31),
                     addi(base=7), addi(base=1),
                     addi(opcode=15), COPY, GUARD):
            with self.subTest(word=word):
                with self.assertRaises(ValueError):
                    promote(*self.inputs(word))
        # Even a saved nonvolatile destination is rejected for native parity.
        self.mask = 1 << 16
        with self.assertRaisesRegex(ValueError, 'report immediate encoding'):
            promote(*self.inputs(addi(dst=16)))

    def test_following_guard_and_invalid_words(self):
        for word in (GUARD, -1, 0x100000000, True, None, 'code'):
            with self.subTest(word=word):
                with self.assertRaisesRegex(ValueError, 'report immediate successor'):
                    promote(*self.inputs(following=word))

    def test_tampered_copy_and_predecessor_refused(self):
        copy, predecessor, compare, following = self.inputs()
        blocks, fields = copy
        wrong = [
            ({**blocks, ROOT: blocks[ROOT][:-1] + (0,)}, fields),
            (blocks, fields[:-1] + (ROOT + 16,)),
            (blocks, fields[:4] + (addi(5),) + fields[5:]),
        ]
        for replacement in wrong:
            with self.subTest(replacement=replacement[1][-4:]):
                with self.assertRaises(ValueError):
                    promote(replacement, predecessor, compare, following)
        gp = list(self.gp)
        gp[7] = ('reg', 7)
        with self.assertRaises(ValueError):
            promote(copy, (self.byte, tuple(gp), 0), compare, following)

    def test_sibling_preservation_and_new_span_collision(self):
        sibling = ROOT + 0x200
        self.byte = ({ROOT: (LOAD, COMPARE, GUARD),
                      sibling: (0x60000000, GUARD)}, self.byte[1])
        contract = promote(*self.inputs())
        self.assertEqual(contract[0][sibling], (0x60000000, GUARD))
        self.assertEqual(len(contract[0]), 2)
        # Existing predecessor was valid at +16..+19; the new +20
        # test-only guard cannot overwrite an unrelated sibling root.
        sibling = ROOT + 20
        self.byte = ({ROOT: (LOAD, COMPARE, GUARD),
                      sibling: (0x60000000, GUARD)}, self.byte[1])
        with self.assertRaises(ValueError):
            promote(*self.inputs())

    def test_plan_reuses_authenticated_predecessor(self):
        expected = self.inputs()
        with patch('prepare_formatter_report_immediate_fixture.byte_plan',
                   return_value=expected[1]) as b, \
             patch('prepare_formatter_report_immediate_fixture.compare_plan',
                   return_value=expected[2]) as c, \
             patch('prepare_formatter_report_immediate_fixture.copy_plan',
                   return_value=expected[0]) as d, \
             patch('prepare_formatter_report_immediate_fixture.parse_functions',
                   return_value={ROOT: 24}), \
             patch('prepare_formatter_report_immediate_fixture.exact_words',
                   return_value=(LOAD, COMPARE, COPY, addi(), NEXT)):
            contract = plan(b'original fixture', b'elf')
        b.assert_called_once_with(b'original fixture', b'elf', with_live=True)
        c.assert_called_once_with(b'original fixture', b'elf',
                                  predecessor=expected[1])
        d.assert_called_once_with(b'original fixture', b'elf',
                                  predecessor=expected[1], compare=expected[2])
        self.assertEqual(contract[0][ROOT][-2:], (NEXT, GUARD))

    def test_plan_extent_and_original_history(self):
        copy, predecessor, compare, following = self.inputs()
        with patch('prepare_formatter_report_immediate_fixture.parse_functions',
                   return_value={ROOT: 20}):
            with self.assertRaisesRegex(ValueError, 'extent'):
                plan(b'dol', b'elf', predecessor=predecessor,
                     compare=compare, copy=copy)
        with patch('prepare_formatter_report_immediate_fixture.parse_functions',
                   return_value={ROOT: 24}), \
             patch('prepare_formatter_report_immediate_fixture.exact_words',
                   return_value=(LOAD, COMPARE, COPY ^ 1, addi(), NEXT)):
            with self.assertRaisesRegex(ValueError, 'original'):
                plan(b'dol', b'elf', predecessor=predecessor,
                     compare=compare, copy=copy)

    def test_121_native_harness_has_exact_fourth_guard_call_chain(self):
        # The full game harness is intentionally compiled only on the
        # private owner. Catch missing optional witness arguments and a
        # missing guard in the public fixture tests instead.
        import re
        path = Path(__file__).with_name(
            'test_native_scheduler_postack_v1256.cpp')
        source = path.read_text()
        # Preserve the exact nested preprocessor guard hierarchy.
        # The 122–125 extensions must be nested behind their own flags.
        # In a 121-only build no later optional instruction is passed.
        fourth = (r'\s*#ifdef UNDERCOVER_FORMATTER_CALLER_REPORT_FOURTH_IMMEDIATE'
                  r'\s*,formatter_report_fourth_immediate_private::next_word'
                  r'\s*#endif')
        third = (r'\s*#ifdef UNDERCOVER_FORMATTER_CALLER_REPORT_THIRD_IMMEDIATE'
                 r'\s*,formatter_report_third_immediate_private::next_word'
                 r'(?:' + fourth + r')?'
                 r'\s*#endif')
        second = (r'\s*#ifdef UNDERCOVER_FORMATTER_CALLER_REPORT_SECOND_IMMEDIATE'
                  r'\s*,formatter_report_second_immediate_private::next_word'
                  r'(?:' + third + r')?'
                  r'\s*#endif')
        expected = (r'#ifdef UNDERCOVER_FORMATTER_CALLER_REPORT_IMMEDIATE'
                    r'\s*,formatter_report_immediate_private::next_word'
                    r'(?:\s*#ifdef UNDERCOVER_FORMATTER_CALLER_REPORT_SIGNEXT'
                    r'\s*,formatter_report_signext_private::next_word'
                    r'(?:' + second + r')?'
                    r'\s*#endif)?\s*#endif')
        for opening, ending in (
            ('!formatter_nested->resume_caller_next_entry(c,',
             '))formatter_nested_refuse(2);'),
            ('!formatter_report_byte->arm_native(',
             '||'),
            ('!formatter_report_compare->arm(',
             '||'),
        ):
            with self.subTest(call=opening):
                self.assertEqual(source.count(opening), 1)
                fragment = source.split(opening,1)[1].split(ending,1)[0]
                self.assertRegex(fragment,expected)
                self.assertEqual(fragment.count(
                    'formatter_report_immediate_private::next_word'),1)
        self.assertIn('if(formatter_nested->stage()==36u)',source)
        self.assertIn('!formatter_nested->resume_caller_report_immediate(',source)
        self.assertIn('!formatter_nested->stop_after_caller_report_immediate(',source)
        self.assertIn(
            'c.mmu.write32(formatter_report_immediate_private::next_pc+4u,0x44000002u);',
            source)
        self.assertIn('nested.caller_report_immediate_visits()==1u',source)
        self.assertIn('immediates_verified=8',source)
        scopes = []
        for number,line in enumerate(source.splitlines(),1):
            m = re.match(r'\s*#\s*(if|ifdef|ifndef|elif|else|endif)\b',line)
            if not m:
                continue
            if m[1] in ('if','ifdef','ifndef'):
                scopes.append(number)
            elif m[1]=='endif':
                self.assertTrue(scopes,f'unmatched endif: {number}')
                scopes.pop()
            else:
                self.assertTrue(scopes,f'unmatched preprocessor else: {number}')
        self.assertEqual(scopes,[])

    def test_121_runner_mode_is_separate_from_verified_120(self):
        runner=Path(__file__).with_name(
            'run_v1256_native_scheduler_postack.sh').read_text()
        self.assertIn('--formatter-nested-caller-report-immediate',runner)
        self.assertIn('nested_args=(--caller-report-immediate)',runner)
        self.assertIn('-DUNDERCOVER_FORMATTER_CALLER_REPORT_IMMEDIATE',runner)
        fixture=Path(__file__).with_name(
            'prepare_formatter_nested_fixture.py').read_text()
        for fragment in (
            "modes.add_argument('--caller-report-immediate'",
            'if q.caller_report_immediate:q.caller_report_copy=True',
            'immediate_contract=report_immediate_plan(',
            'immediate_extension(expanded,copy_contract,immediate_contract)',
            'immediate_extension(final,copy_contract,immediate_contract)',
            'else 32 if second_immediate_contract is not None else 28 if signext_contract is not None else 24 if immediate_contract is not None',
        ):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment,fixture)

    def test_generated_private_header_is_valid_cpp(self):
        compiler = shutil.which('g++')
        if not compiler:
            self.skipTest('no g++ compiler')
        header = render(promote(*self.inputs()))
        source = '#include <cstdint>\n' + header + """
using namespace formatter_report_immediate_private;
static_assert(pc==root+12u);
static_assert(next_pc==root+16u);
static_assert(destination_reg==3u);
static_assert(value==0xfffffffeu);
int main(){return 0;}
"""
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/'source_only.cpp'
            path.write_text(source)
            result = subprocess.run(
                [compiler, '-std=c++20', '-Wall', '-Wextra', '-Werror',
                 '-fsyntax-only', str(path)],
                text=True, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_render_refuses_forged_contract(self):
        original = promote(*self.inputs())
        blocks, fields = original
        variants = [
            fields[:6] + (True,) + fields[7:],
            fields[:5] + (14,) + fields[6:],
            fields[:4] + (GUARD,) + fields[5:],
            fields[:7] + (ROOT + 20,),
            fields[:2] + (addi(base=3),) + fields[3:],
        ]
        for forged in variants:
            with self.subTest(forged=forged[-4:]):
                with self.assertRaisesRegex(ValueError, 'rendering'):
                    render((blocks, forged))


if __name__ == '__main__':
    unittest.main(verbosity=2)
