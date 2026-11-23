#!/usr/bin/env python3
"""V381 audit rejects mixed, unordered and private data disclosure."""
import tempfile
import unittest
from pathlib import Path
from analyze_v381_nand_ipc_handler import inspect
from diagnose_v299_native_log import WINDOW
E='V381_NAND_IPC_ENTRY registered=1 context=1 abi=1 y1=1 masked=1 advanced=1\n'
T='V381_NAND_IPC_TRIAL scheduler=1 ipc=1 completed=1\n'
def run(raw,rc=0):
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'private-guest-binary.log'
        path.write_text(raw,encoding='utf-8')
        return inspect(path,rc)
class Tests(unittest.TestCase):
    def test_original_registered_ipc_evidence(self):
        result=run('guest secret original register words\n'+E+T)
        self.assertIn('entries=1 trials=1 entry_any=1 trial_any=1 ipc_verified=1',result)
        self.assertNotIn('guest secret',result)
        self.assertNotIn('private-guest',result)
    def test_missing_false_mixed_or_unordered_cannot_pass(self):
        for s in ('',E,T,E+E+T,T+E+T,E+T+T,
                  E.replace('registered=1','registered=0')+T,
                  E+T+E.replace('context=1','context=0')+T,
                  E+T+E+T.replace('completed=1','completed=0')):
            self.assertIn('ipc_verified=0',run(s),s)
    def test_large_log_does_not_claim_completeness(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'private.log'
            with path.open('wb') as f:
                f.write((E+T).encode('ascii'))
                f.seek(WINDOW+80)
                f.write(b'\n')
            result=inspect(path,124)
            self.assertIn('sample_complete=0',result)
            self.assertIn('ipc_verified=1',result)
if __name__=='__main__':
    unittest.main()
