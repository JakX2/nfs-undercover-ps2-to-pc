#!/usr/bin/env python3
"""V386 original-free privacy-safe positive and negative evidence tests."""
import tempfile
import unittest
from pathlib import Path
from analyze_v386_nand_ipc_next import inspect
from diagnose_v299_native_log import WINDOW
E='V386_NAND_NEXT_ENTRY guest=1 registered=1 masked=1 signal=1 writer=1 cache=0\n'
T='V386_NAND_NEXT_TRIAL stopped=1 next=1 completed=1\n'
def run(raw,rc=0):
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'private-original-data.log'
        p.write_text(raw,encoding='utf-8')
        return inspect(p,rc)
class Tests(unittest.TestCase):
    def test_original_guest_call_and_optional_writer_classification(self):
        result=run('private registers withheld\n'+E+T)
        self.assertIn('entries=1 trials=1 signal_any=1 writer_any=1 cache_any=0 next_verified=1',result)
        self.assertNotIn('private registers',result)
        self.assertNotIn('private-original-data',result)
        unknown=run(E.replace('writer=1','writer=0')+T)
        self.assertIn('writer_any=0',unknown)
        self.assertIn('next_verified=1',unknown)
    def test_missing_or_mixed_evidence_fails_closed(self):
        for text in ('',E,T,E+E+T,T+E+T,E+T+T,
                     E+T+E.replace('masked=1','masked=0')+T,
                     E.replace('registered=1','registered=0')+T,
                     E+T+E+T.replace('completed=1','completed=0')):
            self.assertIn('next_verified=0',run(text),text)
    def test_incomplete_sample_never_claimed_exhaustive(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'private.log'
            with p.open('wb') as f:
                f.write((E+T).encode('ascii'))
                f.seek(WINDOW+90)
                f.write(b'\n')
            self.assertIn('sample_complete=0',inspect(p,124))
if __name__=='__main__':
    unittest.main()
