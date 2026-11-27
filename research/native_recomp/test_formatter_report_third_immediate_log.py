#!/usr/bin/env python3
"""Source-only exact 992-visit marker contract for future original 124 execution."""
import unittest
from pathlib import Path

from validate_formatter_nested_log import mixed_markers, verify

ARGS=dict(
    caller_report_third_immediate=True,
    integer_count=2,post_integer_count=1,
    mixed_integers=2,mixed_taken=2,mixed_fallthrough=1,
)


def valid_log():
    tag,trial,total=mixed_markers(
        2,1,2,2,1,third_immediate=True)
    records=[trial.pattern.replace('([0-7])',str(i)) for i in range(8)]
    return tag,records+[total],total


class Original124LogTests(unittest.TestCase):
    def test_exact_native_124_eight_trials_and_visits(self):
        tag,lines,total=valid_log()
        self.assertEqual(tag,'FORMATTER_CALLER_REPORT_THIRD_IMMEDIATE')
        for marker in ('third_immediates_verified=8',
                       'second_immediates_verified=8',
                       'signexts_verified=8','immediates_verified=8',
                       'total_visits=992',
                       'fallback=0 complete_image=0 boot_verified=0'):
            self.assertIn(marker,total)
        self.assertEqual(verify(lines,**ARGS),(total,))

    def test_stale_native_logs_and_mutated_metrics_are_not_124_proof(self):
        _,lines,total=valid_log()
        for bad in (
            lines[:-1], lines[1:], lines+[lines[0]],
            [*lines,'FORMATTER_NESTED_REFUSAL code=6'],
            [*lines[:-1],total.replace('total_visits=992','total_visits=984')],
            [*lines[:-1],total.replace('total_visits=992','total_visits=976')],
            [*lines[:-1],total.replace('third_immediates_verified=8',
                                      'third_immediates_verified=7')],
            [*lines[:-1],total.replace('fallback=0','fallback=1')],
            [*lines[:-1],total.replace(
                'FORMATTER_CALLER_REPORT_THIRD_IMMEDIATE_NATIVE',
                'FORMATTER_CALLER_REPORT_SECOND_IMMEDIATE_NATIVE')],
            [*lines[:4],lines[4].replace(
                'third_immediate_verified=1','third_immediate_verified=0'),
             *lines[5:]],
            [*lines[:4],lines[4].replace(
                'total_visits=124','total_visits=123'),*lines[5:]],
        ):
            with self.subTest(bad=bad[-1][:80]):
                with self.assertRaises(ValueError):
                    verify(bad,**ARGS)

    def test_known_runtime_failure_markers_reject_valid_124_aggregate(self):
        # The real 123 attempt emitted a generic V1256_OPEN_FAILURE.
        # Neither that line nor its redacted source-line diagnostic may
        # coexist with an accepted native 124 witness, regardless of where
        # the failure occurs in the log.
        _, valid, _ = valid_log()
        failures = (
            'V1256_OPEN_FAILURE kind=witness trial=0 stage=8 reason=0 line=0',
            'V1256_WITNESS_SOURCE source_line=1511 original_data=0',
            'FORMATTER_NESTED_REFUSAL kind=2 stage=40',
            'FORMATTER_CALLER_FRAME_LEASE_REFUSAL stage=40',
            'FORMATTER_CALLER_REPORT_THIRD_IMMEDIATE_REFUSAL stage=43',
            'FORMATTER_NESTED_FAILURE trial=0',
            'V1256 execution failed rc=1',
        )
        for marker in failures:
            for index in (0, len(valid)//2, len(valid)):
                with self.subTest(marker=marker, index=index):
                    mixed = valid.copy()
                    mixed.insert(index, marker)
                    with self.assertRaisesRegex(ValueError, 'native refusal'):
                        verify(mixed, **ARGS)

    def test_non_failure_metadata_does_not_create_false_refusal(self):
        _, valid, total = valid_log()
        # The validator deliberately ignores unrelated status records in
        # the full owner log, but not any recognized failure family.
        neutral = (
            'V1256_OPEN_FAILURE_ARCHIVE field=redacted',
            'V1256_SCHED_TRIAL n=0 waiting=1',
            'LOG_NOTE V1256_WITNESS_SOURCE archived=1',
        )
        self.assertEqual(verify([*valid, *neutral], **ARGS), (total,))

    def test_all_earlier_modes_reject_124_log(self):
        _,lines,_=valid_log()
        for field in ('caller_report_second_immediate',
                      'caller_report_signext',
                      'caller_report_immediate',
                      'caller_report_copy'):
            with self.subTest(mode=field):
                kwargs={**ARGS,'caller_report_third_immediate':False,
                        field:True}
                with self.assertRaises(ValueError):
                    verify(lines,**kwargs)
        with self.assertRaisesRegex(ValueError,'native mode'):
            verify(lines,**{**ARGS,'caller_report_second_immediate':True})
        with self.assertRaises(ValueError):
            verify(lines,**{**ARGS,'mixed_taken':1})

    def test_source_only_parser_and_native_fixture_mode_connected(self):
        root=Path(__file__).parent
        parser=(root/'validate_formatter_nested_log.py').read_text()
        nested=(root/'prepare_formatter_nested_fixture.py').read_text()
        required=(
            'third_immediate=caller_report_third_immediate',
            "m.add_argument('--caller-report-third-immediate',action='store_true')",
            'third_immediates_verified=8',
            "FORMATTER_CALLER_REPORT_THIRD_IMMEDIATE",
        )
        for marker in required:
            with self.subTest(marker=marker):
                self.assertIn(marker,parser)
        for marker in (
            "modes.add_argument('--caller-report-third-immediate',action='store_true')",
            'third_immediate_extension(final,second_immediate_contract,third_immediate_contract)',
            'third_immediate_contract=third_immediate_contract',
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker,nested)


if __name__=='__main__':
    unittest.main()
