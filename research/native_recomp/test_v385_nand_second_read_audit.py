#!/usr/bin/env python3
"""V385 strict privacy-safe second original IPC reader tests."""
import tempfile
import unittest
from pathlib import Path
from analyze_v385_nand_second_read import inspect
from diagnose_v299_native_log import WINDOW
E='V385_NAND_SECOND_READ caller=1 irq=1 registered=1 masked=1 advanced=1\n'
T='V385_NAND_SECOND_READ_TRIAL first=1 second=1 completed=1\n'
def run(raw,rc=0):
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'private-original-code.log'
        p.write_text(raw,encoding='utf-8')
        return inspect(p,rc)
class Tests(unittest.TestCase):
    def test_original_second_read_positive_and_private(self):
        result=run('confidential original register address\n'+E+T)
        self.assertIn('entries=1 trials=1 entry_any=1 trial_any=1 second_read_verified=1',result)
        self.assertNotIn('confidential original',result)
        self.assertNotIn('private-original',result)
    def test_mixed_or_out_of_order_not_verified(self):
        for s in ('',E,T,E+E+T,T+E+T,E+T+T,
                  E.replace('masked=1','masked=0')+T,
                  E+T+E.replace('caller=1','caller=0')+T,
                  E+T+E+T.replace('completed=1','completed=0')):
            self.assertIn('second_read_verified=0',run(s),s)
    def test_bounded_sample_indicated(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'private.log'
            with p.open('wb') as f:
                f.write((E+T).encode('ascii'))
                f.seek(WINDOW+40)
                f.write(b'\n')
            self.assertIn('sample_complete=0',inspect(p,124))
if __name__=='__main__':
    unittest.main()
