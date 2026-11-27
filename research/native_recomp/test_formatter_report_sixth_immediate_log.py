#!/usr/bin/env python3
"""Original-free, exact native 127 instruction marker and refusal tests."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from validate_formatter_nested_log import mixed_markers, verify

ARGS = dict(caller_report_sixth_immediate=True, integer_count=2,
            post_integer_count=1, mixed_integers=2, mixed_taken=2,
            mixed_fallthrough=1)


def valid_log():
    tag, trial, total = mixed_markers(
        2, 1, 2, 2, 1, sixth_immediate=True)
    records = [trial.pattern.replace('([0-7])', str(i)) for i in range(8)]
    return tag, records+[total], total


class Original127LogTests(unittest.TestCase):
    def test_exact_1016_visits_and_all_predecessor_witnesses(self):
        tag, records, total = valid_log()
        self.assertEqual(tag, 'FORMATTER_CALLER_REPORT_SIXTH_IMMEDIATE')
        self.assertEqual(verify(records, **ARGS), (total,))
        for expected in (
            'sixth_immediates_verified=8',
            'fifth_immediates_verified=8',
            'fourth_immediates_verified=8',
            'total_visits=1016', 'fallback=0 complete_image=0 boot_verified=0',
        ):
            self.assertIn(expected, total)
        for record in records[:-1]:
            self.assertIn('total_visits=127', record)
            self.assertIn('sixth_immediate_verified=1', record)

    def test_corruptions_missing_trials_duplicates_and_mode_refused(self):
        _, records, total = valid_log()
        variants = [
            records[:-1],
            records[1:],
            records+[records[0]],
            records[:-1]+[total.replace('total_visits=1016','total_visits=1008')],
            records[:-1]+[total.replace('fallback=0','fallback=1')],
            records[:-1]+[total.replace('sixth_immediates_verified=8',
                                       'sixth_immediates_verified=7')],
            records[:3]+[records[3].replace('sixth_immediate_verified=1',
                                           'sixth_immediate_verified=0')]+records[4:],
        ]
        for candidate in variants:
            with self.subTest(last=candidate[-1][:60]):
                with self.assertRaises(ValueError):
                    verify(candidate, **ARGS)
        with self.assertRaisesRegex(ValueError, 'native mode'):
            verify(records, **{**ARGS,'caller_report_fifth_immediate':True})
        with self.assertRaises(ValueError):
            verify(records, **{**ARGS,'caller_report_sixth_immediate':False,
                               'caller_report_fifth_immediate':True})

    def test_refusal_preempts_success(self):
        _, records, _ = valid_log()
        for refusal in (
            'FORMATTER_NESTED_REFUSAL kind=2 stage=48',
            'FORMATTER_CALLER_FRAME_LEASE_REFUSAL stage=48',
            'V1256 execution failed rc=1',
        ):
            with self.subTest(refusal=refusal):
                with self.assertRaisesRegex(ValueError,'native refusal'):
                    verify([records[0], refusal]+records[1:], **ARGS)

    def test_cpp_trial_precedence_prevents_misattributed_126_native_proof(self):
        # The original 126 owner run failed its exact trial contract because
        # the 125 selector was checked before the 126 selector. This check
        # prevents another source-only pass that only fails on owner binaries.
        source = (Path(__file__).parent /
                  'test_native_scheduler_postack_v1256.cpp').read_text()
        start = source.index('#if defined(UNDERCOVER_FORMATTER_CALLER_MIXED)\\n'
                             '            std::cout<<')
        chunk = source[start:start+1600]
        expected = (
            '#if defined(UNDERCOVER_FORMATTER_CALLER_REPORT_SIXTH_IMMEDIATE)',
            '"FORMATTER_CALLER_REPORT_SIXTH_IMMEDIATE_TRIAL n="',
            '#elif defined(UNDERCOVER_FORMATTER_CALLER_REPORT_FIFTH_IMMEDIATE)',
            '"FORMATTER_CALLER_REPORT_FIFTH_IMMEDIATE_TRIAL n="',
            '#elif defined(UNDERCOVER_FORMATTER_CALLER_REPORT_FOURTH_IMMEDIATE)',
            '"FORMATTER_CALLER_REPORT_FOURTH_IMMEDIATE_TRIAL n="',
        )
        offsets = [chunk.find(marker) for marker in expected]
        self.assertTrue(all(i >= 0 for i in offsets), offsets)
        self.assertEqual(offsets, sorted(offsets))
        self.assertEqual(chunk.count('REPORT_SIXTH_IMMEDIATE_TRIAL n='), 1)
        self.assertEqual(chunk.count('REPORT_FIFTH_IMMEDIATE_TRIAL n='), 1)

    def test_cli_and_dispatch_guard_wiring(self):
        _, records, total = valid_log()
        root = Path(__file__).parent
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'log.txt'
            path.write_text('\n'.join(records)+'\n')
            res = subprocess.run(
                [sys.executable,str(root/'validate_formatter_nested_log.py'),
                 str(path),'--caller-report-sixth-immediate',
                 '--integer-count','2','--post-integer-count','1',
                 '--mixed-integers','2','--mixed-taken','2',
                 '--mixed-fallthrough','1'],
                capture_output=True,text=True,check=False)
            self.assertEqual(res.returncode,0,res.stdout+res.stderr)
            self.assertEqual(res.stdout.strip(),total)
        harness = (root/'test_native_scheduler_postack_v1256.cpp').read_text()
        for marker in (
            'FORMATTER_CALLER_REPORT_SIXTH_IMMEDIATE_TRIAL n=',
            'FORMATTER_CALLER_REPORT_SIXTH_IMMEDIATE_NATIVE',
            'sixth_immediates_verified=8',
            'resume_caller_report_sixth_immediate(c,',
            'stop_after_caller_report_sixth_immediate(c,pc,w,held)',
        ):
            self.assertIn(marker,harness)
        runner = (root/'run_v1256_native_scheduler_postack.sh').read_text()
        self.assertIn('--formatter-nested-caller-report-sixth-immediate',runner)
        self.assertIn('nested_args=(--caller-report-sixth-immediate)',runner)


if __name__ == '__main__':
    unittest.main(verbosity=2)
