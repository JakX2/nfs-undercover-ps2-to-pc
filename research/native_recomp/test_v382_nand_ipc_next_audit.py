#!/usr/bin/env python3
"""V382 next-call audit rejects mixed or out-of-order original-trace evidence."""
import tempfile
import unittest
from pathlib import Path
from analyze_v382_nand_ipc_next import inspect
from diagnose_v299_native_log import WINDOW
E='V382_NAND_IPC_NEXT guest=1 registered=1 masked=1 advanced=1 known=1 signal=1\n'
T='V382_NAND_IPC_TRIAL ipc=1 next=1 completed=1\n'
def run(raw,rc=0):
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'private-raw.log'
        path.write_text(raw,encoding='utf-8')
        return inspect(path,rc)
class Tests(unittest.TestCase):
    def test_private_trace_not_exposed(self):
        report=run('secret addr instruction bytes\n'+E+T)
        self.assertIn('entries=1 trials=1 known_any=1 signal_any=1 next_verified=1',report)
        self.assertNotIn('secret addr',report)
        self.assertNotIn('private-raw',report)
    def test_unknown_helper_still_reports_verified_original_guest_call(self):
        report=run(E.replace('known=1','known=0')+T)
        self.assertIn('known_any=0',report)
        self.assertIn('next_verified=1',report)
    def test_malformed_mixed_and_unpaired_are_not_verified(self):
        for raw in ('',E,T,E+E+T,T+E+T,E+T+T,
                    E.replace('masked=1','masked=0')+T,
                    E+T+E.replace('registered=1','registered=0')+T,
                    E+T+E+T.replace('completed=1','completed=0')):
            self.assertIn('next_verified=0',run(raw),raw)
    def test_bounded_truncation_disclosed(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'private.log'
            with p.open('wb') as f:
                f.write((E+T).encode('ascii'))
                f.seek(WINDOW+200)
                f.write(b'\n')
            report=inspect(p,124)
            self.assertIn('sample_complete=0',report)
            self.assertIn('next_verified=1',report)
if __name__=='__main__':
    unittest.main()
