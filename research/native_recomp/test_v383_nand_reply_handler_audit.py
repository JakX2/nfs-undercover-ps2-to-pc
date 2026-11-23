#!/usr/bin/env python3
"""V383 public-only original NAND IpcReplyHandler proof tests."""
import tempfile
import unittest
from pathlib import Path
from analyze_v383_nand_reply_handler import inspect
from diagnose_v299_native_log import WINDOW
E='V383_NAND_REPLY_ENTRY read=1 caller=1 registered=1 irq=1 masked=1 advanced=1\n'
T='V383_NAND_REPLY_TRIAL next=1 reply=1 completed=1\n'
def run(raw,rc=0):
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'private-original-broadway.log'
        p.write_text(raw,encoding='utf-8')
        return inspect(p,rc)
class Tests(unittest.TestCase):
    def test_real_guest_trace_census_no_private_leak(self):
        result=run('secret game instruction bytes\n'+E+T)
        self.assertIn('entries=1 trials=1 entry_any=1 trial_any=1 reply_handler_verified=1',result)
        self.assertNotIn('secret game',result)
        self.assertNotIn('private-original',result)
    def test_malformed_mixed_or_unpaired_cannot_prove_reply(self):
        for item in ('',E,T,E+E+T,T+E+T,E+T+T,
                     E.replace('registered=1','registered=0')+T,
                     E.replace('read=1','read=0')+T,
                     E+T+E+T.replace('completed=1','completed=0')):
            self.assertIn('reply_handler_verified=0',run(item),item)
    def test_truncation_reported(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'private.log'
            with p.open('wb') as f:
                f.write((E+T).encode('ascii'))
                f.seek(WINDOW+120)
                f.write(b'\n')
            result=inspect(p,124)
            self.assertIn('sample_complete=0',result)
            self.assertIn('reply_handler_verified=1',result)
if __name__=='__main__':
    unittest.main()
