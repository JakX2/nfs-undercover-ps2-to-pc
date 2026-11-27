#!/usr/bin/env python3
"""Source-only regression: the 119 native CR stages retain redacted refusal logs."""
import re
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name('run_v1256_native_scheduler_postack.sh')


def refusal_expression():
    matches = [
        line for line in SCRIPT.read_text().splitlines()
        if line.startswith("grep -Ex 'FORMATTER_NESTED_REFUSAL ")
    ]
    if len(matches) != 1:
        raise ValueError('native refusal filter count')
    # The grep alternation is ERE, compatible with Python for this fixed
    # pattern; no owner data or log paths are read.
    line = matches[0]
    return line.split("'", 2)[1]


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
    def test_comparison_refusal_stages_are_visible(self):
        pattern = refusal_expression()
        for stage in range(34):
            with self.subTest(stage=stage):
                self.assertIsNotNone(re.fullmatch(pattern, sample(stage)))
        for stage in (34, 35, 40, -1):
            with self.subTest(stage=stage):
                self.assertIsNone(re.fullmatch(pattern, sample(stage)))

    def test_filter_refuses_untrusted_shape(self):
        pattern = refusal_expression()
        for corrupted in (
            sample(32, kind=8), sample(32, reason=7),
            sample(33, branches=5), sample(33, visits=1234),
            sample(32) + ' pc=0x80000000',
            sample(33).replace('stage=33 ', 'stage=33 private_word=0 '),
            'FORMATTER_NESTED_REFUSAL stage=32',
        ):
            with self.subTest(record=corrupted[:45]):
                self.assertIsNone(re.fullmatch(pattern, corrupted))


if __name__ == '__main__':
    unittest.main(verbosity=2)
