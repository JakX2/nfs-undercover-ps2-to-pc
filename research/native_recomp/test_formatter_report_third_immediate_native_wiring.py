#!/usr/bin/env python3
"""Source-only harness wiring checks for original instruction-124 native lane.

This test cannot prove owner execution. It proves that the opt-in runner,
source guard, native witness, parent-frame lease and exact log validator
are connected, and refuses removed or unguarded predecessor stages.
"""
import unittest
from pathlib import Path

from validate_formatter_nested_log import mixed_markers, verify

ROOT=Path(__file__).parent
EXPECTED_MODE=dict(
    caller_report_third_immediate=True,
    integer_count=2,post_integer_count=1,
    mixed_integers=2,mixed_taken=2,mixed_fallthrough=1,
)


class Original124NativeWiring(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runner=(ROOT/'run_v1256_native_scheduler_postack.sh').read_text()
        cls.harness=(ROOT/'test_native_scheduler_postack_v1256.cpp').read_text()
        cls.frame=(ROOT/'wii_post_stm_sc_formatter.h').read_text()
        cls.byte=(ROOT/'wii_formatter_report_byte_transition.h').read_text()
        cls.cmp=(ROOT/'wii_formatter_caller_integer.h').read_text()
        cls.fixture=(ROOT/'prepare_formatter_nested_fixture.py').read_text()

    def test_strict_opt_in_flag_and_fixture_selection(self):
        for marker in (
            '--formatter-nested-caller-report-third-immediate',
            'formatter_caller_report_third_immediate_mode=1',
            '-DUNDERCOVER_FORMATTER_CALLER_REPORT_THIRD_IMMEDIATE',
            'nested_args=(--caller-report-third-immediate)',
            'formatter_caller_report_second_immediate_mode=1',
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker,self.runner)
        self.assertIn(
            "modes.add_argument('--caller-report-third-immediate',action='store_true')",
            self.fixture)
        self.assertIn(
            'if q.caller_report_third_immediate:q.caller_report_second_immediate=True',
            self.fixture)

    def test_native_step_has_observer_and_preserves_125_guard(self):
        for marker in (
            '#include "wii_formatter_report_third_immediate.h"',
            'static std::optional<FormatterThirdImmediateWitness> formatter_report_third_immediate;',
            'formatter_report_third_immediate.emplace();',
            'formatter_report_third_immediate->arm(c,',
            'formatter_report_third_immediate->observe(c,pc,w)',
            'formatter_nested->resume_caller_report_third_immediate(c,',
            'formatter_nested->stop_after_caller_report_third_immediate(c,pc,w,held)',
            'formatter_report_third_immediate.reset();',
            'if(formatter_nested->stage()==42u)',
            'formatter_report_third_immediate_private::next_pc+4u,0x44000002u',
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker,self.harness)
        self.assertEqual(self.harness.count(
            'formatter_report_third_immediate->observe(c,pc,w)'),1)
        self.assertEqual(self.harness.count(
            'formatter_nested->stop_after_caller_report_third_immediate(c,pc,w,held)'),1)
        self.assertIn('if(formatter_nested->stage()==40u)',self.harness)
        self.assertIn('formatter_report_second_immediate->observe(c,pc,w)',
                      self.harness)

    def test_ancestor_and_guest_register_guards_survive(self):
        for marker in (
            'resume_caller_report_third_immediate(',
            'stop_after_caller_report_third_immediate(',
            'caller_report_third_immediate_visits()',
            'reached_caller_report_third_immediate(',
            'reached_caller_report_second_immediate(c,held)',
            'predict_caller_zero_input_addi(',
            'stage_=42u;',
            'stage_=43u;',
            'pc!=next_entry_pc_+28u',
            '!report_byte_storage(c,held,7u)',
            'next_entry_seventh_',
            'unsigned(report_third_immediate_completed_)+unsigned(report_fourth_immediate_completed_)+unsigned(report_fifth_immediate_completed_)+unsigned(report_sixth_immediate_completed_)+unsigned(branch_128_completed_)+unsigned(armed)',
            'stage_<=51u',
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker,self.frame)

    def test_seventh_guard_reaches_all_independent_observers(self):
        for marker in (
            'std::optional<uint32_t> seventh_original = {}',
            'native_seventh_ = seventh_original',
            'native_seventh_&&!word(c,step_.pc+32u,native_eighth_.value_or(0x44000002u))',
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker,self.byte)
        for marker in (
            'std::optional<uint32_t> sixth_original={}',
            'sixth_=sixth_original',
            'sixth_&&!word(c,label+24u,seventh_.value_or(0x44000002u))',
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker,self.cmp)

    def test_exact_native_124_marker_wiring_and_123_isolation(self):
        tag,trial,total=mixed_markers(2,1,2,2,1,third_immediate=True)
        self.assertEqual(tag,'FORMATTER_CALLER_REPORT_THIRD_IMMEDIATE')
        self.assertIn('total_visits=992',total)
        self.assertIn('fallback=0 complete_image=0 boot_verified=0',total)
        lines=[trial.pattern.replace('([0-7])',str(i)) for i in range(8)]
        self.assertEqual(verify(lines+[total],**EXPECTED_MODE),(total,))
        for marker in (
            'FORMATTER_CALLER_REPORT_THIRD_IMMEDIATE_TRIAL n=',
            'FORMATTER_CALLER_REPORT_THIRD_IMMEDIATE_NATIVE',
            'third_immediate_verified=',
            'third_immediates_verified=8',
            'nested.caller_report_third_immediate_visits()==1u',
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker,self.harness)
        self.assertIn('FORMATTER_CALLER_REPORT_SECOND_IMMEDIATE_TRIAL n=',self.harness)
        self.assertIn('FORMATTER_CALLER_REPORT_SECOND_IMMEDIATE_NATIVE',self.harness)
        self.assertIn('nested.caller_report_second_immediate_visits()==1u',self.harness)
        old_tag,old_trial,old_total=mixed_markers(2,1,2,2,1,second_immediate=True)
        self.assertIn('total_visits=984',old_total)
        old_lines=[old_trial.pattern.replace('([0-7])',str(i)) for i in range(8)]
        self.assertEqual(
            verify(old_lines+[old_total],**{
                **EXPECTED_MODE,
                'caller_report_third_immediate':False,
                'caller_report_second_immediate':True,
            }),
            (old_total,))


if __name__=='__main__':
    unittest.main()
