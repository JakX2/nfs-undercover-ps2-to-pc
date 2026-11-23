#!/usr/bin/env python3
"""V379 public-only timebase audit must fail on mixed or unordered evidence."""
import tempfile
import unittest
from pathlib import Path
from analyze_v379_nand_timebase_frontier import inspect
from diagnose_v299_native_log import WINDOW
E='V379_NAND_TIME_ENTRY guest=1 signal=1 masked=1 progressed=1 resume=1\n'
T='V379_NAND_TIME_TRIAL dispatch=1 time=1 completed=1\n'
def run(text,rc=0):
    with tempfile.TemporaryDirectory() as root:
        path=Path(root)/'private-original-bytes.log'
        path.write_text(text,encoding='utf-8')
        return inspect(path,rc)
class Tests(unittest.TestCase):
    def test_single_original_timebase_handoff(self):
        report=run('private-PC-r3-unknown\n'+E+T)
        self.assertIn('entries=1 trials=1 entry_any=1 trial_any=1 guest_time_verified=1',report)
        self.assertNotIn('private-PC',report)
        self.assertNotIn('private-original',report)
    def test_mixed_or_unmatched_evidence_does_not_pass(self):
        for sample in (
            '',E,T,E+E+T,T+E+T,E+T+E+T.replace('completed=1','completed=0'),
            E+T+E.replace('masked=1','masked=0')+T,
            E.replace('guest=1','guest=0')+T,
            E+T+T
        ):
            self.assertIn('guest_time_verified=0',run(sample),sample)
    def test_truncation_does_not_claim_complete_sample(self):
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/'private.log'
            with path.open('wb') as f:
                f.write((E+T).encode('ascii'))
                f.seek(WINDOW+100)
                f.write(b'\n')
            report=inspect(path,124)
            self.assertIn('sample_complete=0',report)
            self.assertIn('guest_time_verified=1',report)
if __name__=='__main__':
    unittest.main()
