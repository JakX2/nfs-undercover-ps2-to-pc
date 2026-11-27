#!/usr/bin/env python3
"""Source-only native 126 guarded runner, parent lease and log integration.

No private owner code, emulator or translated original instruction runs here.
"""
import subprocess
import unittest
from pathlib import Path

from validate_formatter_nested_log import mixed_markers, verify

ROOT = Path(__file__).parent
ARGS = dict(
    caller_report_fifth_immediate=True,
    integer_count=2, post_integer_count=1,
    mixed_integers=2, mixed_taken=2, mixed_fallthrough=1,
)


class Original126NativeWiring(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        names = {
            'runner': 'run_v1256_native_scheduler_postack.sh',
            'harness': 'test_native_scheduler_postack_v1256.cpp',
            'frame': 'wii_post_stm_sc_formatter.h',
            'byte': 'wii_formatter_report_byte_transition.h',
            'compare': 'wii_formatter_caller_integer.h',
            'second': 'wii_formatter_report_second_immediate.h',
            'third': 'wii_formatter_report_third_immediate.h',
            'fourth': 'wii_formatter_report_fourth_immediate.h',
            'fifth': 'wii_formatter_report_fifth_immediate.h',
            'signext': 'wii_formatter_report_signext.h',
            'fixture': 'prepare_formatter_nested_fixture.py',
        }
        for name, file_name in names.items():
            setattr(cls, name, (ROOT / file_name).read_text())

    def test_mode_is_strictly_opt_in_and_keeps_125_parent(self):
        for marker in (
            '--formatter-nested-caller-report-fifth-immediate',
            'formatter_caller_report_fifth_immediate_mode=1',
            '--formatter-nested-caller-report-fourth-immediate',
            '-DUNDERCOVER_FORMATTER_CALLER_REPORT_FIFTH_IMMEDIATE',
            'nested_args=(--caller-report-fifth-immediate)',
            'formatter_caller_report_fourth_immediate_mode=1',
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, self.runner)
        subprocess.run(['bash', '-n', str(ROOT / 'run_v1256_native_scheduler_postack.sh')],
                       check=True, capture_output=True)
        for marker in (
            "modes.add_argument('--caller-report-fifth-immediate',action='store_true')",
            'if q.caller_report_fifth_immediate:q.caller_report_fourth_immediate=True',
            'fifth_immediate_extension(final,fourth_immediate_contract,fifth_immediate_contract)',
        ):
            self.assertIn(marker, self.fixture)

    def test_only_aot_execution_can_complete_fifth_witness(self):
        for marker in (
            '#include "wii_formatter_report_fifth_immediate.h"',
            'static std::optional<FormatterFifthImmediateWitness> formatter_report_fifth_immediate;',
            'formatter_report_fifth_immediate.emplace();',
            'formatter_report_fifth_immediate->arm(c,',
            'formatter_report_fifth_immediate->observe(c,pc,w)',
            'formatter_nested->resume_caller_report_fifth_immediate(c,',
            'formatter_nested->stop_after_caller_report_fifth_immediate(c,pc,w,held)',
            'formatter_report_fifth_immediate.reset();',
            'if(formatter_nested->stage()==46u)',
            'formatter_report_fifth_immediate_private::next_pc+4u,0x44000002u',
            'return; // the original translated addi for instruction 126 executes',
            'fifth_immediates_verified=8',
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, self.harness)
        self.assertEqual(self.harness.count(
            'formatter_report_fifth_immediate->observe(c,pc,w)'), 1)
        self.assertEqual(self.harness.count(
            'formatter_nested->stop_after_caller_report_fifth_immediate(c,pc,w,held)'), 1)
        self.assertIn('if(formatter_nested->stage()==44u)', self.harness)
        self.assertIn('formatter_report_fourth_immediate->observe(c,pc,w)', self.harness)
        self.assertIn('formatter_report_fifth_immediate_private::word==',
                      self.harness)
        # Direct 125 -> 126 source continuity is a compile-time contract.
        # Never accidentally compare the fifth word against original 124.
        fifth_asserts = self.harness.split(
            '#ifdef UNDERCOVER_FORMATTER_CALLER_REPORT_FIFTH_IMMEDIATE\n'
            'static_assert(', 1)[1].split('#endif', 1)[0]
        self.assertEqual(fifth_asserts.count(
            'formatter_report_fourth_immediate_private::'), 4)
        self.assertNotIn('formatter_report_third_immediate_private::',
                         fifth_asserts)

    def test_parent_lease_requires_exact_ninth_label(self):
        for marker in (
            'resume_caller_report_fifth_immediate(',
            'stop_after_caller_report_fifth_immediate(',
            'caller_report_fifth_immediate_visits()',
            'reached_caller_report_fifth_immediate(',
            'reached_caller_report_fourth_immediate(c,held)',
            'predict_caller_zero_input_addi(',
            'stage_=46u;', 'stage_=47u;',
            'pc!=next_entry_pc_+36u',
            '!report_byte_storage(c,held,9u)',
            'next_entry_ninth_', '(ninth&&!eighth)',
            'stage_<=51u', 'stage_==46u',
            'unsigned(report_fifth_immediate_completed_)+unsigned(report_sixth_immediate_completed_)+unsigned(branch_128_completed_)+unsigned(armed)',
            'if(n>43u)return {};',
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, self.frame)
        self.assertIn('!next_entry_ninth_||word(c,next_entry_pc_+40u,next_entry_tenth_.value_or(0x44000002u))',
                      self.frame)
        self.assertIn('!next_entry_eighth_||word(c,next_entry_pc_+36u,next_entry_ninth_.value_or(0x44000002u))',
                      self.frame)

    def test_all_earlier_witnesses_preserve_moved_stop_guard(self):
        for marker in (
            'std::optional<uint32_t> ninth_original = {}',
            'native_ninth_ = ninth_original',
            'native_eighth_&&!word(c,step_.pc+36u,native_ninth_.value_or(0x44000002u))',
            'native_ninth_&&!word(c,step_.pc+40u,native_tenth_.value_or(0x44000002u))',
        ):
            self.assertIn(marker, self.byte)
        for marker in (
            'std::optional<uint32_t> eighth_original={}',
            'eighth_=eighth_original',
            'seventh_&&!word(c,label+28u,eighth_.value_or(0x44000002u))',
            'eighth_&&!word(c,label+32u,ninth_.value_or(0x44000002u))',
        ):
            self.assertIn(marker, self.compare)
        for marker in (
            'std::optional<uint32_t> fifth={}',
        ):
            self.assertIn(marker, self.second)
            self.assertIn(marker, self.signext)
        for marker in ('tail_matches(c,pc,following,trailing,fourth,fifth)',
                       '!fifth||word(c,pc+24u,0x44000002u)'):
            self.assertIn(marker, self.second)
        for marker in ('tail_matches(c,pc,following,trailing,fourth,fifth,sixth)',
                       '!fifth||word(c,pc+24u,sixth.value_or(0x44000002u))'):
            self.assertIn(marker, self.signext)
        for marker in (
            'std::optional<uint32_t> trailing={}',
            'tail_matches(c,pc,following,trailing,fourth)',
            '!trailing||word(c,pc+16u,fourth.value_or(0x44000002u))',
        ):
            self.assertIn(marker, self.third)
        self.assertIn('std::optional<uint32_t> following={}', self.fourth)
        self.assertIn('tail_matches(c,pc,following,trailing)', self.fourth)
        for marker in (
            'pc!=root+32u',
            'c.inst_count!=count_+1u',
            'c.gqr!=gqr_',
            'c.srr0!=srr0_',
            'c.srr1!=srr1_',
        ):
            self.assertIn(marker, self.fifth)

    def test_exact_native_126_markers_and_125_independence(self):
        tag, trial, total = mixed_markers(
            2, 1, 2, 2, 1, fifth_immediate=True)
        self.assertEqual(tag, 'FORMATTER_CALLER_REPORT_FIFTH_IMMEDIATE')
        self.assertIn('total_visits=1008', total)
        records = [trial.pattern.replace('([0-7])', str(i)) for i in range(8)]
        self.assertEqual(verify(records + [total], **ARGS), (total,))
        for marker in (
            'FORMATTER_CALLER_REPORT_FIFTH_IMMEDIATE_TRIAL n=',
            'FORMATTER_CALLER_REPORT_FIFTH_IMMEDIATE_NATIVE',
            'fifth_immediate_verified=',
            'fifth_immediates_verified=8',
            'nested.caller_report_fifth_immediate_visits()==1u',
        ):
            # Every required trial tag must exist in the compiled
            # branch selector, not merely in a synthetic log validator.
            self.assertIn(marker, self.harness)
        fifth = self.harness.index(
            'FORMATTER_CALLER_REPORT_FIFTH_IMMEDIATE_TRIAL n=')
        fourth = self.harness.index(
            'FORMATTER_CALLER_REPORT_FOURTH_IMMEDIATE_TRIAL n=')
        self.assertLess(fifth, fourth)
        self.assertIn(
            '#elif defined(UNDERCOVER_FORMATTER_CALLER_REPORT_FIFTH_IMMEDIATE)',
            self.harness)
        self.assertIn('FORMATTER_CALLER_REPORT_FOURTH_IMMEDIATE_NATIVE',
                      self.harness)
        self.assertIn('nested.caller_report_fourth_immediate_visits()==1u',
                      self.harness)


if __name__ == '__main__':
    unittest.main(verbosity=2)
