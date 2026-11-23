#!/usr/bin/env python3
"""V389 public-only original Hollywood W1C proof cannot accept mixed evidence."""
import tempfile
import unittest
from pathlib import Path
from analyze_v389_nand_hollywood_ack import inspect
from diagnose_v299_native_log import WINDOW
E='V389_NAND_FLAG_ACK before=1 wrote=1 cleared=1 down=1 y1=1 guest=1 registered=1\n'
T='V389_NAND_FLAG_TRIAL y1=1 flag=1 completed=1\n'
def run(s):
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'private-original-wii.log'
        p.write_text(s,encoding='utf-8')
        return inspect(p,0)
class Tests(unittest.TestCase):
    def test_two_separate_original_guest_w1c_events(self):
        report=run('secret game registers\n'+E+T)
        self.assertIn('entries=1 trials=1 flag_ack_verified=1',report)
        self.assertNotIn('secret game',report)
    def test_missing_mixed_unordered_and_false_rejected(self):
        for x in ('',E,T,E+E+T,T+E+T,E+T+T,
                  E.replace('cleared=1','cleared=0')+T,
                  E.replace('y1=1','y1=0')+T,
                  E+T+E+T.replace('completed=1','completed=0')):
            self.assertIn('flag_ack_verified=0',run(x),x)
    def test_truncation_explicit(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'private.log'
            with p.open('wb') as f:
                f.write((E+T).encode('ascii'))
                f.seek(WINDOW+62)
                f.write(b'\n')
            self.assertIn('sample_complete=0',inspect(p,124))
if __name__=='__main__':unittest.main()
