#!/usr/bin/env python3
"""V380 original-free audit of real NAND guest scheduler handoff."""
import tempfile
import unittest
from pathlib import Path
from analyze_v380_nand_scheduler_frontier import inspect
from diagnose_v299_native_log import WINDOW
E='V380_NAND_SCHED_ENTRY guest=1 irq=1 masked=1 advanced=1 sda=1\n'
T='V380_NAND_SCHED_TRIAL time=1 scheduler=1 completed=1\n'
def run(source,rc=0):
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'private-game-source-raw.log'
        path.write_text(source,encoding='utf-8')
        return inspect(path,rc)
class Tests(unittest.TestCase):
    def test_valid_pair_redacts_all_private_data(self):
        s=run('secret guest register snapshot\n'+E+T)
        self.assertIn('entries=1 trials=1 entry_any=1 trial_any=1 scheduler_verified=1',s)
        self.assertNotIn('secret guest',s)
        self.assertNotIn('private-game-source',s)
    def test_unpaired_unordered_or_mixed_bad_cannot_verify(self):
        for sample in ('',E,T,E+E+T,T+E+T,E+T+T,
                       E+T+E.replace('masked=1','masked=0')+T,
                       E.replace('guest=1','guest=0')+T,
                       E+T+E+T.replace('completed=1','completed=0')):
            self.assertIn('scheduler_verified=0',run(sample),sample)
    def test_truncated_large_log_marked_incomplete(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'private.log'
            with path.open('wb') as f:
                f.write((E+T).encode('ascii'))
                f.seek(WINDOW+24)
                f.write(b'\n')
            s=inspect(path,124)
            self.assertIn('sample_complete=0',s)
            self.assertIn('scheduler_verified=1',s)
if __name__=='__main__':
    unittest.main()
