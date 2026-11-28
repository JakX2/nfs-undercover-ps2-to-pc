#!/usr/bin/env python3
"""Source-only native 125 runner, lease and log integration checks.

This does not authenticate or execute original game code.
"""
import unittest
from pathlib import Path

from validate_formatter_nested_log import mixed_markers, verify

ROOT = Path(__file__).parent
ARGS = dict(
    caller_report_fourth_immediate=True,
    integer_count=2, post_integer_count=1,
    mixed_integers=2, mixed_taken=2, mixed_fallthrough=1,
)


class Original125NativeWiring(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        names = {
            'runner': 'run_v1256_native_scheduler_postack.sh',
            'harness': 'test_native_scheduler_postack_v1256.cpp',
            'frame': 'wii_post_stm_sc_formatter.h',
            'byte': 'wii_formatter_report_byte_transition.h',
            'compare': 'wii_formatter_caller_integer.h',
            'second': 'wii_formatter_report_second_immediate.h',
            'signext': 'wii_formatter_report_signext.h',
            'fixture': 'prepare_formatter_nested_fixture.py',
        }
        for name, file_name in names.items():
            setattr(cls, name, (ROOT / file_name).read_text())

    def test_mode_is_explicit_and_preserves_124_predecessor(self):
        for marker in (
            '--formatter-nested-caller-report-fourth-immediate',
            'formatter_caller_report_fourth_immediate_mode=1',
            '--formatter-nested-caller-report-third-immediate',
            '-DUNDERCOVER_FORMATTER_CALLER_REPORT_FOURTH_IMMEDIATE',
            'nested_args=(--caller-report-fourth-immediate)',
            'formatter_caller_report_third_immediate_mode=1',
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, self.runner)
        for marker in (
            "modes.add_argument('--caller-report-fourth-immediate',action='store_true')",
            'if q.caller_report_fourth_immediate:q.caller_report_third_immediate=True',
            'fourth_immediate_extension(final,third_immediate_contract,fourth_immediate_contract)',
        ):
            self.assertIn(marker, self.fixture)

    def test_step_is_native_observed_and_never_software_executed(self):
        for marker in (
            '#include "wii_formatter_report_fourth_immediate.h"',
            'static std::optional<FormatterFourthImmediateWitness> formatter_report_fourth_immediate;',
            'formatter_report_fourth_immediate.emplace();',
            'formatter_report_fourth_immediate->arm(c,',
            'formatter_report_fourth_immediate->observe(c,pc,w)',
            'formatter_nested->resume_caller_report_fourth_immediate(c,',
            'formatter_nested->stop_after_caller_report_fourth_immediate(c,pc,w,held)',
            'formatter_report_fourth_immediate.reset();',
            'if(formatter_nested->stage()==44u)',
            'formatter_report_fourth_immediate_private::next_pc+4u,0x44000002u',
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, self.harness)
        self.assertEqual(self.harness.count(
            'formatter_report_fourth_immediate->observe(c,pc,w)'), 1)
        self.assertEqual(self.harness.count(
            'formatter_nested->stop_after_caller_report_fourth_immediate(c,pc,w,held)'), 1)
        self.assertIn('if(formatter_nested->stage()==42u)', self.harness)
        self.assertIn('formatter_report_third_immediate->observe(c,pc,w)', self.harness)
        self.assertIn('return; // the original translated addi for instruction 125 executes',
                      self.harness)

    def test_parent_frame_lease_is_bounded_and_guarded(self):
        for marker in (
            'resume_caller_report_fourth_immediate(',
            'stop_after_caller_report_fourth_immediate(',
            'caller_report_fourth_immediate_visits()',
            'reached_caller_report_fourth_immediate(',
            'reached_caller_report_third_immediate(c,held)',
            'predict_caller_zero_input_addi(',
            'stage_=44u;', 'stage_=45u;',
            'pc!=next_entry_pc_+32u',
            '!report_byte_storage(c,held,8u)',
            'next_entry_eighth_', 'eighth&&!seventh',
            'stage_<=53u',
            'unsigned(report_fourth_immediate_completed_)+unsigned(report_fifth_immediate_completed_)+unsigned(report_sixth_immediate_completed_)+unsigned(branch_128_completed_)+unsigned(compare_129_completed_)+unsigned(armed)',
            'if(n>43u)return {};',
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, self.frame)

    def test_all_earlier_witnesses_authenticate_moved_guards(self):
        for marker in (
            'std::optional<uint32_t> eighth_original = {}',
            'native_eighth_ = eighth_original',
            'native_seventh_&&!word(c,step_.pc+32u,native_eighth_.value_or(0x44000002u))',
            'native_eighth_&&!word(c,step_.pc+36u,native_ninth_.value_or(0x44000002u))',
        ):
            self.assertIn(marker, self.byte)
        for marker in (
            'std::optional<uint32_t> seventh_original={}',
            'seventh_=seventh_original',
            'sixth_&&!word(c,label+24u,seventh_.value_or(0x44000002u))',
            'seventh_&&!word(c,label+28u,eighth_.value_or(0x44000002u))',
        ):
            self.assertIn(marker, self.compare)
        for marker in (
            'std::optional<uint32_t> fourth={}',
            '!fourth||word(c,pc+20u,fifth.value_or(0x44000002u))',
        ):
            self.assertIn(marker, self.second)
            self.assertIn(marker, self.signext)
        # Second immediate retains its five-word tail, whereas signext
        # carries one more authenticated successor for the 127 opt-in path.
        self.assertIn(
            'tail_matches(c,pc,following,trailing,fourth,fifth)',
            self.second)
        self.assertIn(
            'tail_matches(c,pc,following,trailing,fourth,fifth,sixth)',
            self.signext)

    def test_125_markers_and_earlier_log_modes_remain_independent(self):
        tag, trial, total = mixed_markers(2, 1, 2, 2, 1,
                                          fourth_immediate=True)
        self.assertEqual(tag, 'FORMATTER_CALLER_REPORT_FOURTH_IMMEDIATE')
        self.assertIn('total_visits=1000', total)
        lines = [trial.pattern.replace('([0-7])', str(i)) for i in range(8)]
        self.assertEqual(verify(lines + [total], **ARGS), (total,))
        for marker in (
            'FORMATTER_CALLER_REPORT_FOURTH_IMMEDIATE_TRIAL n=',
            'FORMATTER_CALLER_REPORT_FOURTH_IMMEDIATE_NATIVE',
            'fourth_immediate_verified=',
            'fourth_immediates_verified=8',
            'nested.caller_report_fourth_immediate_visits()==1u',
        ):
            self.assertIn(marker, self.harness)
        for older in ('third', 'second'):
            self.assertIn(
                'FORMATTER_CALLER_REPORT_' + older.upper() + '_IMMEDIATE_NATIVE',
                self.harness)
        self.assertIn('nested.caller_report_third_immediate_visits()==1u',
                      self.harness)


if __name__ == '__main__':
    unittest.main(verbosity=2)
