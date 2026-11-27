#!/usr/bin/env python3
"""Original-free exact 1008-visit log contract for future original 126 AOT."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from validate_formatter_nested_log import mixed_markers, verify

ARGS = dict(
    caller_report_fifth_immediate=True,
    integer_count=2, post_integer_count=1,
    mixed_integers=2, mixed_taken=2, mixed_fallthrough=1,
)


def valid_log():
    tag, trial, total = mixed_markers(
        2, 1, 2, 2, 1, fifth_immediate=True)
    records = [trial.pattern.replace('([0-7])', str(i)) for i in range(8)]
    return tag, records + [total], total


class Original126LogTests(unittest.TestCase):
    def test_exact_native_126_trial_contract(self):
        tag, records, total = valid_log()
        self.assertEqual(tag, 'FORMATTER_CALLER_REPORT_FIFTH_IMMEDIATE')
        for marker in ('fifth_immediates_verified=8',
                       'fourth_immediates_verified=8',
                       'third_immediates_verified=8',
                       'second_immediates_verified=8',
                       'signexts_verified=8',
                       'total_visits=1008',
                       'fallback=0 complete_image=0 boot_verified=0'):
            self.assertIn(marker, total)
        self.assertEqual(verify(records, **ARGS), (total,))
        for record in records[:-1]:
            self.assertIn('total_visits=126', record)

    def test_125_and_earlier_native_modes_do_not_prove_126(self):
        _, records, total = valid_log()
        for earlier in ('fourth_immediate', 'third_immediate',
                        'second_immediate', 'signext', 'immediate', 'copy'):
            with self.subTest(mode=earlier):
                field = 'caller_report_' + earlier
                kwargs = {**ARGS, 'caller_report_fifth_immediate': False,
                          field: True}
                with self.assertRaises(ValueError):
                    verify(records, **kwargs)
        for previous in ('fourth_immediate', 'third_immediate',
                         'second_immediate', 'signext'):
            _, pattern, old_total = mixed_markers(
                2, 1, 2, 2, 1, **{previous: True})
            old_lines = [pattern.pattern.replace('([0-7])', str(i))
                         for i in range(8)] + [old_total]
            with self.subTest(previous=previous):
                with self.assertRaises(ValueError):
                    verify(old_lines, **ARGS)
        with self.assertRaisesRegex(ValueError, 'native mode'):
            verify(records, **{**ARGS, 'caller_report_fourth_immediate': True})
        self.assertIn('total_visits=1008', total)

    def test_truncation_duplicate_fallback_and_mutations_rejected(self):
        _, lines, total = valid_log()
        candidates = [
            lines[:-1], lines[1:], lines + [lines[0]],
            [*lines[:-1], total.replace('total_visits=1008',
                                        'total_visits=1000')],
            [*lines[:-1], total.replace('total_visits=1008',
                                        'total_visits=992')],
            [*lines[:-1], total.replace(
                'fifth_immediates_verified=8', 'fifth_immediates_verified=7')],
            [*lines[:-1], total.replace('fallback=0', 'fallback=1')],
            [*lines[:3], lines[3].replace(
                'fifth_immediate_verified=1', 'fifth_immediate_verified=0'),
             *lines[4:]],
            [*lines[:5], lines[5].replace(
                'total_visits=126', 'total_visits=125'), *lines[6:]],
            [*lines[:-1], total.replace(
                'FORMATTER_CALLER_REPORT_FIFTH_IMMEDIATE_NATIVE',
                'FORMATTER_CALLER_REPORT_FOURTH_IMMEDIATE_NATIVE')],
            [*lines[:-1], total + ' extra=private'],
        ]
        for candidate in candidates:
            with self.subTest(last=candidate[-1][:80]):
                with self.assertRaises(ValueError):
                    verify(candidate, **ARGS)

    def test_runtime_failure_markers_override_complete_log(self):
        _, lines, _ = valid_log()
        failures = (
            'V1256_OPEN_FAILURE kind=witness trial=0 stage=8 reason=0 line=0',
            'V1256_WITNESS_SOURCE source_line=1511 original_data=0',
            'FORMATTER_NESTED_REFUSAL kind=2 stage=46',
            'FORMATTER_CALLER_REPORT_FIFTH_IMMEDIATE_REFUSAL stage=47',
            'FORMATTER_CALLER_FRAME_LEASE_REFUSAL stage=46',
            'V1256 execution failed rc=1',
        )
        for failure in failures:
            for index in (0, 4, len(lines)):
                with self.subTest(failure=failure, at=index):
                    candidate = lines.copy()
                    candidate.insert(index, failure)
                    with self.assertRaisesRegex(ValueError, 'native refusal'):
                        verify(candidate, **ARGS)

    def test_actual_cli_contract_and_error_exit(self):
        root = Path(__file__).parent
        program = root / 'validate_formatter_nested_log.py'
        _, lines, total = valid_log()
        flags = ('--caller-report-fifth-immediate',
                 '--integer-count', '2', '--post-integer-count', '1',
                 '--mixed-integers', '2', '--mixed-taken', '2',
                 '--mixed-fallthrough', '1')
        with tempfile.TemporaryDirectory() as temp:
            log = Path(temp) / 'log.txt'
            log.write_text('\n'.join(lines) + '\n')
            ok = subprocess.run(
                [sys.executable, str(program), str(log), *flags],
                capture_output=True, text=True, check=False)
            self.assertEqual(ok.returncode, 0, ok.stdout + ok.stderr)
            self.assertEqual(ok.stdout.strip(), total)
            log.write_text('\n'.join([
                *lines[:-1], total.replace('total_visits=1008',
                                           'total_visits=1000')]) + '\n')
            bad = subprocess.run(
                [sys.executable, str(program), str(log), *flags],
                capture_output=True, text=True, check=False)
            self.assertNotEqual(bad.returncode, 0)
            self.assertIn('verified=0', bad.stdout)

    def test_source_only_parser_and_native_handoff_wired(self):
        root = Path(__file__).parent
        parser = (root / 'validate_formatter_nested_log.py').read_text()
        fixture = (root / 'prepare_formatter_nested_fixture.py').read_text()
        for marker in (
            'fifth_immediate=caller_report_fifth_immediate',
            "m.add_argument('--caller-report-fifth-immediate',action='store_true')",
            'fifth_immediates_verified=8',
            'FORMATTER_CALLER_REPORT_FIFTH_IMMEDIATE',
        ):
            self.assertIn(marker, parser)
        for marker in (
            "modes.add_argument('--caller-report-fifth-immediate',action='store_true')",
            'fifth_immediate_extension(final,fourth_immediate_contract,fifth_immediate_contract)',
            'fifth_immediate_contract=fifth_immediate_contract',
        ):
            self.assertIn(marker, fixture)


if __name__ == '__main__':
    unittest.main(verbosity=2)
