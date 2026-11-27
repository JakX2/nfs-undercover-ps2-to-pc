#!/usr/bin/env python3
"""Source-only exact 976-visit instruction-122 log regressions."""
import unittest

from validate_formatter_nested_log import mixed_markers, verify

ARGS = dict(
    caller_report_signext=True, integer_count=2, post_integer_count=1,
    mixed_integers=2, mixed_taken=2, mixed_fallthrough=1,
)


def valid_log():
    tag, trial, total = mixed_markers(2, 1, 2, 2, 1, signext=True)
    records = [trial.pattern.replace('([0-7])', str(n))
               for n in range(8)]
    return tag, records + [total], total


class Original122LogTests(unittest.TestCase):
    def test_exact_122_marker_and_976_visits(self):
        tag, lines, total = valid_log()
        self.assertEqual(tag, 'FORMATTER_CALLER_REPORT_SIGNEXT')
        self.assertIn('signexts_verified=8', total)
        self.assertIn('immediates_verified=8', total)
        self.assertIn('total_visits=976', total)
        self.assertIn('fallback=0 complete_image=0 boot_verified=0', total)
        result = verify(lines, **ARGS)
        self.assertEqual(result, (total,))

    def test_reject_121_log_and_all_missing_or_duplicate_trials(self):
        tag, lines, total = valid_log()
        for bad in (
                lines[:-1], lines[1:], lines + [lines[0]],
                [*lines, 'FORMATTER_NESTED_REFUSAL code=6'],
                [*lines[:-1], total.replace('total_visits=976',
                                           'total_visits=968')],
                [*lines[:-1], total.replace('signexts_verified=8',
                                           'signexts_verified=7')],
                [*lines[:-1], total.replace('fallback=0', 'fallback=1')],
                [*lines[:-1],
                 total.replace('FORMATTER_CALLER_REPORT_SIGNEXT_NATIVE',
                               'FORMATTER_CALLER_REPORT_IMMEDIATE_NATIVE')],
                [*lines[:3], lines[3].replace('signext_verified=1',
                                              'signext_verified=0'),
                 *lines[4:]],
                [*lines[:3], lines[3].replace('total_visits=122',
                                              'total_visits=121'),
                 *lines[4:]],
        ):
            with self.subTest(bad=bad[-1][:80]):
                with self.assertRaises(ValueError):
                    verify(bad, **ARGS)

    def test_no_other_mode_admits_the_122_marker(self):
        _, lines, _ = valid_log()
        with self.assertRaises(ValueError):
            verify(lines, caller_report_immediate=True,
                   integer_count=2, post_integer_count=1,
                   mixed_integers=2, mixed_taken=2, mixed_fallthrough=1)
        with self.assertRaisesRegex(ValueError, 'native mode'):
            verify(lines, **{**ARGS, 'caller_report_immediate': True})
        with self.assertRaises(ValueError):
            verify(lines, **{**ARGS, 'mixed_taken': 1})

    def test_runner_and_harness_opt_in_contract(self):
        from pathlib import Path
        root = Path(__file__).parent
        runner = (root / 'run_v1256_native_scheduler_postack.sh').read_text()
        harness = (root / 'test_native_scheduler_postack_v1256.cpp').read_text()
        fixture = (root / 'prepare_formatter_nested_fixture.py').read_text()
        for fragment in (
                '--formatter-nested-caller-report-signext',
                'formatter_caller_report_signext_mode=1',
                '-DUNDERCOVER_FORMATTER_CALLER_REPORT_SIGNEXT',
                'nested_args=(--caller-report-signext)'):
            self.assertIn(fragment, runner)
        for fragment in (
                'formatter_nested->stage()==38u',
                'formatter_report_signext->observe(c,pc,w)',
                'formatter_nested->stop_after_caller_report_signext(',
                'formatter_report_signext_private::next_pc+4u,0x44000002u',
                'nested.caller_report_signext_visits()==1u',
                'signexts_verified=8',
                'FORMATTER_CALLER_REPORT_SIGNEXT_NATIVE'):
            self.assertIn(fragment, harness)
        self.assertIn('--caller-report-signext', fixture)


if __name__ == '__main__':
    unittest.main()
