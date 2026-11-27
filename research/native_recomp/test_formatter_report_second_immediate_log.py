#!/usr/bin/env python3
"""Source-only regression: exact 984-visit original 123 native marker."""
import unittest
from pathlib import Path
from validate_formatter_nested_log import mixed_markers, verify

ARGS=dict(
    caller_report_second_immediate=True,
    integer_count=2,post_integer_count=1,
    mixed_integers=2,mixed_taken=2,mixed_fallthrough=1,
)


def valid_log():
    tag,trial,total=mixed_markers(
        2,1,2,2,1,second_immediate=True)
    records=[trial.pattern.replace('([0-7])',str(i)) for i in range(8)]
    return tag,records+[total],total


class Original123LogTests(unittest.TestCase):
    def test_exact_native_123_eight_trials_and_visits(self):
        tag,lines,total=valid_log()
        self.assertEqual(tag,'FORMATTER_CALLER_REPORT_SECOND_IMMEDIATE')
        self.assertIn('second_immediates_verified=8',total)
        self.assertIn('signexts_verified=8',total)
        self.assertIn('immediates_verified=8',total)
        self.assertIn('total_visits=984',total)
        self.assertIn('fallback=0 complete_image=0 boot_verified=0',total)
        self.assertEqual(verify(lines,**ARGS),(total,))

    def test_older_native_log_is_not_123_proof(self):
        tag,lines,total=valid_log()
        for bad in (
            lines[:-1], lines[1:], lines+[lines[0]],
            [*lines,'FORMATTER_NESTED_REFUSAL code=6'],
            [*lines[:-1],total.replace('total_visits=984',
                                      'total_visits=976')],
            [*lines[:-1],total.replace('second_immediates_verified=8',
                                      'second_immediates_verified=7')],
            [*lines[:-1],total.replace('fallback=0','fallback=1')],
            [*lines[:-1],total.replace(
                'FORMATTER_CALLER_REPORT_SECOND_IMMEDIATE_NATIVE',
                'FORMATTER_CALLER_REPORT_SIGNEXT_NATIVE')],
            [*lines[:4],lines[4].replace('second_immediate_verified=1',
                                        'second_immediate_verified=0'),
             *lines[5:]],
            [*lines[:4],lines[4].replace('total_visits=123',
                                        'total_visits=122'),*lines[5:]],
        ):
            with self.subTest(bad=bad[-1][:80]):
                with self.assertRaises(ValueError):
                    verify(bad,**ARGS)

    def test_mode_is_not_admitted_by_122_or_121_validator(self):
        _,lines,_=valid_log()
        for kwargs in (
            dict(caller_report_signext=True),
            dict(caller_report_immediate=True),
        ):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(ValueError):
                    verify(lines,**{
                        **ARGS,
                        'caller_report_second_immediate':False,
                        **kwargs,
                    })
        with self.assertRaisesRegex(ValueError,'native mode'):
            verify(lines,**{**ARGS,'caller_report_signext':True})
        with self.assertRaises(ValueError):
            verify(lines,**{**ARGS,'mixed_taken':1})

    def test_native_runner_and_witness_are_opt_in(self):
        root=Path(__file__).parent
        runner=(root/'run_v1256_native_scheduler_postack.sh').read_text()
        nested=(root/'prepare_formatter_nested_fixture.py').read_text()
        header=(root/'wii_post_stm_sc_formatter.h').read_text()
        harness=(root/'test_native_scheduler_postack_v1256.cpp').read_text()
        for text in (
            '--formatter-nested-caller-report-second-immediate',
            'formatter_caller_report_second_immediate_mode=1',
            '-DUNDERCOVER_FORMATTER_CALLER_REPORT_SECOND_IMMEDIATE',
            'nested_args=(--caller-report-second-immediate)',
        ):
            with self.subTest(text=text):
                self.assertIn(text,runner)
        for text in (
            "modes.add_argument('--caller-report-second-immediate',action='store_true')",
            'second_immediate_extension(final,signext_contract,second_immediate_contract)',
        ):
            self.assertIn(text,nested)
        for text in (
            'resume_caller_report_second_immediate(',
            'stop_after_caller_report_second_immediate(',
            'reached_caller_report_second_immediate(',
            'caller_report_second_immediate_visits()',
        ):
            self.assertIn(text,header)
        for text in (
            'formatter_nested->stage()==40u',
            'formatter_report_second_immediate->observe(c,pc,w)',
            'formatter_nested->stop_after_caller_report_second_immediate(',
            'formatter_report_second_immediate_private::next_pc+4u,0x44000002u',
            'nested.caller_report_second_immediate_visits()==1u',
            'second_immediates_verified=8',
            'FORMATTER_CALLER_REPORT_SECOND_IMMEDIATE_NATIVE',
            'formatter_report_second_immediate.emplace()',
        ):
            with self.subTest(text=text):
                self.assertIn(text,harness)


if __name__=='__main__':
    unittest.main()
