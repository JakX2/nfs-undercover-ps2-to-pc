#!/usr/bin/env python3
"""Source-only regression: native continuation stages retain strictly redacted refusal logs."""
import re
import subprocess
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name('run_v1256_native_scheduler_postack.sh')


def filter_expression(prefix):
    matches = [
        line for line in SCRIPT.read_text().splitlines()
        if line.startswith("grep -Ex '" + prefix + " ")
    ]
    if len(matches) != 1:
        raise ValueError('native refusal filter count')
    # The grep alternation is ERE, compatible with Python for this fixed
    # pattern; no owner data or log paths are read.
    line = matches[0]
    return line.split("'", 2)[1]


def refusal_expression():
    return filter_expression('FORMATTER_NESTED_REFUSAL')


def sample(stage, **fields):
    data = dict(kind=2, stage=stage, reason=6, visits=98, loads=15,
                stores=17, branches=4, post=1, branch_detail=0,
                held_mask=0, parent_age=141, parent_limit=142,
                parent_baseline=140, outer_age=141, outer_limit=142,
                outer_baseline=140)
    data.update(fields)
    keys = ('kind', 'stage', 'reason', 'visits', 'loads', 'stores',
            'branches', 'post', 'branch_detail', 'held_mask',
            'parent_age', 'parent_limit', 'parent_baseline',
            'outer_age', 'outer_limit', 'outer_baseline')
    return 'FORMATTER_NESTED_REFUSAL ' + ' '.join(
        f'{key}={data[key]}' for key in keys)


class RefusalFilterTests(unittest.TestCase):
    def test_all_implemented_refusal_stages_are_visible(self):
        pattern = refusal_expression()
        for stage in range(44):
            with self.subTest(stage=stage):
                self.assertIsNotNone(re.fullmatch(pattern, sample(stage)))
        for stage in (44, 45, 99, -1):
            with self.subTest(stage=stage):
                self.assertIsNone(re.fullmatch(pattern, sample(stage)))

    def test_filter_refuses_untrusted_shape(self):
        pattern = refusal_expression()
        for corrupted in (
            sample(32, kind=8), sample(32, reason=7),
            sample(35, branches=5), sample(34, visits=1234),
            sample(32) + ' pc=0x80000000',
            sample(33).replace('stage=33 ', 'stage=33 private_word=0 '),
            'FORMATTER_NESTED_REFUSAL stage=32',
        ):
            with self.subTest(record=corrupted[:45]):
                self.assertIsNone(re.fullmatch(pattern, corrupted))


    def test_native_source_line_filter_is_strict(self):
        pattern = filter_expression('V1256_WITNESS_SOURCE')
        accepted = [
            'V1256_WITNESS_SOURCE source_line=1 original_data=0',
            'V1256_WITNESS_SOURCE source_line=6326 original_data=0',
            'V1256_WITNESS_SOURCE source_line=99999 original_data=0',
        ]
        rejected = [
            'V1256_WITNESS_SOURCE source_line=0 original_data=0',
            'V1256_WITNESS_SOURCE source_line=100000 original_data=0',
            'V1256_WITNESS_SOURCE source_line=01 original_data=0',
            'V1256_WITNESS_SOURCE source_line=0x80000000 original_data=0',
            'V1256_WITNESS_SOURCE source_line=6326 original_data=1',
            accepted[1] + ' guest_pc=0x80000000',
            'prefix ' + accepted[1],
        ]
        for line in accepted:
            self.assertIsNotNone(re.fullmatch(pattern, line))
        for line in rejected:
            self.assertIsNone(re.fullmatch(pattern, line))
        self.assert_grep_output(pattern, accepted + rejected, accepted)

    def test_actual_grep_preserves_late_refusals(self):
        accepted = [sample(stage) for stage in range(44)]
        rejected = [sample(44), sample(40) + ' guest_pc=0x80000000',
                    sample(42, reason=7), sample(41, kind=8)]
        self.assert_grep_output(refusal_expression(), accepted + rejected, accepted)

    def assert_grep_output(self, pattern, records, accepted):
        result = subprocess.run(
            ['grep', '-Ex', pattern], input='\n'.join(records) + '\n',
            text=True, capture_output=True, check=True)
        self.assertEqual(result.stdout.splitlines(), accepted)
        self.assertEqual(result.stderr, '')


if __name__ == '__main__':
    unittest.main(verbosity=2)
