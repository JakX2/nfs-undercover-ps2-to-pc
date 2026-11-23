#!/usr/bin/env python3
"""V378 original-free audit cannot leak game trace or invent dispatcher."""
import tempfile
import unittest
from pathlib import Path
from analyze_v378_nand_irq_dispatch import inspect
from diagnose_v299_native_log import WINDOW

def run(text,rc=0):
    with tempfile.TemporaryDirectory() as tmp:
        file=Path(tmp)/'private-broadway-raw.log'
        file.write_text(text,encoding='utf-8')
        return inspect(file,rc)
E='V378_NAND_DISPATCH_ENTRY route=1 regs=1 status=1 masked=1 y1=1 advanced=1\n'
T='V378_NAND_DISPATCH_TRIAL handler=1 dispatch=1 completed=1\n'
class Tests(unittest.TestCase):
    def test_genuine_guest_handler_dispatch_pair(self):
        outcome=run('original secret register values\n'+E+T)
        self.assertIn('entries=1 trials=1 entry_any=1 trial_any=1 dispatch_verified=1',outcome)
        self.assertNotIn('secret register',outcome)
        self.assertNotIn('private-broadway',outcome)
    def test_absent_invalid_or_unpaired_cannot_claim_dispatch(self):
        for text in ('',T,'prefix '+E+T,E,E+T.replace('completed=1','completed=0'),
                     E.replace('y1=1','y1=0')+T):
            self.assertIn('dispatch_verified=0',run(text),text)
    def test_mixed_good_bad_or_out_of_order_never_proves_dispatch(self):
        for raw in (
            E+T+E.replace('y1=1','y1=0')+T,
            E.replace('regs=1','regs=0')+T+E+T,
            E+T+E+T.replace('dispatch=1','dispatch=0'),
            E+E+T+T,
            E+T+T,
            T+E+T
        ):
            self.assertIn('dispatch_verified=0',run(raw),raw)
    def test_larger_than_privacy_window_is_reported_incomplete(self):
        with tempfile.TemporaryDirectory() as tmp:
            file=Path(tmp)/'private.log'
            with file.open('wb') as out:
                out.write((E+T).encode('ascii'))
                out.seek(WINDOW+70)
                out.write(b'\n')
            result=inspect(file,124)
            self.assertIn('sample_complete=0',result)
            self.assertIn('dispatch_verified=1',result)
if __name__=='__main__':
    unittest.main()
