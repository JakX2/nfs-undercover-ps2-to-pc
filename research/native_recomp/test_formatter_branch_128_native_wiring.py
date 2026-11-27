#!/usr/bin/env python3
"""Source-only native original-128 taken branch wiring and legacy 127 guards."""
import subprocess
import unittest
from pathlib import Path
from validate_formatter_nested_log import mixed_markers,verify

ROOT=Path(__file__).parent
ARGS=dict(caller_report_branch_128=True,integer_count=2,post_integer_count=1,
          mixed_integers=2,mixed_taken=2,mixed_fallthrough=1)

class Original128NativeWiring(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.harness=(ROOT/'test_native_scheduler_postack_v1256.cpp').read_text()
        cls.runner=(ROOT/'run_v1256_native_scheduler_postack.sh').read_text()
        cls.fixture=(ROOT/'prepare_formatter_nested_fixture.py').read_text()
        cls.parent=(ROOT/'wii_post_stm_sc_formatter.h').read_text()

    def test_strictly_opt_in_and_carries_private_fixture(self):
        for marker in (
            'formatter_caller_report_branch_128_mode=1',
            '--formatter-nested-caller-report-branch-128',
            '-DUNDERCOVER_FORMATTER_CALLER_REPORT_BRANCH_128',
            'nested_args=(--caller-report-branch-128)',
            '--formatter-nested-caller-report-sixth-immediate',
        ):
            with self.subTest(marker=marker):self.assertIn(marker,self.runner)
        subprocess.run(['bash','-n',str(ROOT/'run_v1256_native_scheduler_postack.sh')],
                       check=True,capture_output=True)

    def test_authentic_private_branch_word_and_selected_label(self):
        for marker in (
            '#include "wii_formatter_conditional_branch.h"',
            'static std::optional<FormatterConditionalBranchWitness> formatter_branch_128;',
            'formatter_branch_128_private::word==',
            'formatter_report_sixth_immediate_private::next_word',
            'formatter_branch_128_private::selected_pc',
            'formatter_branch_128_private::selected_word',
            'formatter_branch_128_private::owner_size',
            'formatter_branch_128_private::taken',
            'formatter_branch_128->arm(c,',
            'formatter_branch_128->taken()',
            'formatter_nested->resume_caller_report_branch_128(c,',
            'formatter_branch_128->observe(c,pc,w)',
            'formatter_nested->stop_after_caller_report_branch_128(c,pc,w,held)',
            'formatter_nested->reached_caller_report_branch_128',
            'branch_128_verified=',
            'branches_128_verified=8 branch_taken=8',
        ):
            if marker=='formatter_nested->reached_caller_report_branch_128':
                marker='nested.reached_caller_report_branch_128'
            with self.subTest(marker=marker):self.assertIn(marker,self.harness)
        self.assertEqual(self.harness.count('formatter_branch_128->arm(c,'),1)
        self.assertEqual(self.harness.count('formatter_branch_128->observe(c,pc,w)'),1)
        self.assertIn('if(formatter_nested->stage()==50u)',self.harness)

    def test_parent_128_lease_and_original_127_default(self):
        for marker in ('resume_caller_report_branch_128(',
                       'stop_after_caller_report_branch_128(',
                       'caller_report_branch_128_visits()',
                       'reached_caller_report_branch_128(',
                       'stage_=50u;return true;',
                       'branch_128_completed_=true;stage_=51u;return true;',
                       'report_byte_storage(c,held,11u)'):
            with self.subTest(marker=marker):self.assertIn(marker,self.parent)
        self.assertIn('formatter_report_sixth_immediate_private::next_pc+4u,0x44000002u',
                      self.harness)
        self.assertIn('formatter_report_sixth_immediate->observe(c,pc,w)',
                      self.harness)

    def test_exact_native_128_log_and_trial_precedence(self):
        tag,trial,total=mixed_markers(2,1,2,2,1,branch_128=True)
        self.assertEqual(tag,'FORMATTER_CALLER_REPORT_BRANCH_128')
        self.assertIn('total_visits=1024',total)
        records=[trial.pattern.replace('([0-7])',str(i)) for i in range(8)]
        self.assertEqual(verify(records+[total],**ARGS),(total,))
        a=self.harness.index('FORMATTER_CALLER_REPORT_BRANCH_128_TRIAL n=')
        b=self.harness.index('FORMATTER_CALLER_REPORT_SIXTH_IMMEDIATE_TRIAL n=')
        self.assertLess(a,b)
        self.assertEqual(self.harness.count('FORMATTER_CALLER_REPORT_BRANCH_128_TRIAL n='),1)
        self.assertIn('FORMATTER_CALLER_REPORT_BRANCH_128_NATIVE',self.harness)

if __name__=='__main__':unittest.main(verbosity=2)
