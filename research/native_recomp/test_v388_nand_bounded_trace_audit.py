#!/usr/bin/env python3
"""V388 sanitized bounded call budget evidence is fail-closed."""
import tempfile
import unittest
from pathlib import Path
from analyze_v388_nand_bounded_trace import inspect
from diagnose_v299_native_log import WINDOW
EACK='V388_NAND_BOUNDARY kind=1 verified=1 calls=3 writer=1 read=1 cache=0 y1clear=1 latch=1\n'
EBOUND='V388_NAND_BOUNDARY kind=2 verified=1 calls=16 writer=0 read=1 cache=0 y1clear=0 latch=1\n'
TACK='V388_NAND_BOUNDED_TRIAL kind=1 calls=3 stopped=1 completed=1\n'
TBOUND='V388_NAND_BOUNDED_TRIAL kind=2 calls=16 stopped=1 completed=1\n'
def run(s):
    with tempfile.TemporaryDirectory() as tmp:
        p=Path(tmp)/'proprietary-original-log'
        p.write_text(s,encoding='utf-8')
        return inspect(p,0)
class Tests(unittest.TestCase):
    def test_genuine_y1_ack_and_bounded_guest_calls(self):
        self.assertIn('ack_any=1 bounded_any=0',run(EACK+TACK))
        self.assertIn('bounded_verified=1',run(EACK+TACK))
        self.assertIn('ack_any=0 bounded_any=1',run(EBOUND+TBOUND))
        self.assertIn('bounded_verified=1',run(EBOUND+TBOUND))
    def test_unordered_invalid_or_mixed_never_passes(self):
        for raw in (
            '',EACK,TACK,EBOUND,TBOUND,EACK+TBOUND,
            EBOUND+TACK,EACK+EACK+TACK+TACK,
            EACK+TACK+EBOUND+TACK,
            EACK.replace('latch=1','latch=0')+TACK,
            EBOUND.replace('calls=16','calls=15')+TBOUND,
            EACK+TACK+EBOUND.replace('verified=1','verified=0')+TBOUND
        ):self.assertIn('bounded_verified=0',run(raw),raw)
    def test_no_private_trace_leak(self):
        self.assertNotIn('secret instruction',run('secret instruction\n'+EACK+TACK))
    def test_truncation_exposed(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'private'
            with p.open('wb') as f:
                f.write((EACK+TACK).encode('ascii'))
                f.seek(WINDOW+44)
                f.write(b'\n')
            self.assertIn('sample_complete=0',inspect(p,124))
if __name__=='__main__':unittest.main()
