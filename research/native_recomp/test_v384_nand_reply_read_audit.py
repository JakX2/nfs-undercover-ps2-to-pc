#!/usr/bin/env python3
"""V384 public-only original NAND read checkpoint audit tests."""
import tempfile
import unittest
from pathlib import Path
from analyze_v384_nand_reply_read import inspect
from diagnose_v299_native_log import WINDOW
E='V384_NAND_REPLY_READ caller=1 irq=1 registered=1 masked=1 advanced=1\n'
T='V384_NAND_REPLY_READ_TRIAL reply=1 reader=1 completed=1\n'
def run(raw,rc=0):
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'private-owner-powers.log'
        path.write_text(raw,encoding='utf-8')
        return inspect(path,rc)
class Tests(unittest.TestCase):
    def test_one_valid_genuine_original_reply_read(self):
        result=run('private CPU data not shown\n'+E+T)
        self.assertIn('entries=1 trials=1 entry_any=1 trial_any=1 ipc_read_verified=1',result)
        self.assertNotIn('private CPU',result)
        self.assertNotIn('private-owner',result)
    def test_mixed_unordered_or_missing_fails_closed(self):
        for text in ('',E,T,E+E+T,T+E+T,E+T+T,
                     E.replace('caller=1','caller=0')+T,
                     E+T+E.replace('irq=1','irq=0')+T,
                     E+T+E+T.replace('completed=1','completed=0')):
            self.assertIn('ipc_read_verified=0',run(text),text)
    def test_large_log_bounded_sample_disclosed(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'private.log'
            with path.open('wb') as f:
                f.write((E+T).encode('ascii'))
                f.seek(WINDOW+140)
                f.write(b'\n')
            result=inspect(path,124)
            self.assertIn('sample_complete=0',result)
            self.assertIn('ipc_read_verified=1',result)
if __name__=='__main__':
    unittest.main()
