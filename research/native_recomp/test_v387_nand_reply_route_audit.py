#!/usr/bin/env python3
"""V387 original-free ACK-or-next route evidence audit."""
import tempfile
import unittest
from pathlib import Path
from analyze_v387_nand_reply_route import inspect
from diagnose_v299_native_log import WINDOW
ACK='V387_NAND_ROUTE_EVENT kind=1 verified=1 y1cleared=1 latch=1 writer=1 next=0\n'
NEXT='V387_NAND_ROUTE_EVENT kind=2 verified=1 y1cleared=0 latch=1 writer=0 next=1\n'
TA='V387_NAND_ROUTE_TRIAL kind=1 stopped=1 completed=1\n'
TN='V387_NAND_ROUTE_TRIAL kind=2 stopped=1 completed=1\n'
def go(raw):
    with tempfile.TemporaryDirectory() as td:
        f=Path(td)/'private-native.log'
        f.write_text(raw,encoding='utf-8')
        return inspect(f,0)
class Tests(unittest.TestCase):
    def test_original_ack_and_guest_call_are_independent_evidence(self):
        self.assertIn('ack_any=1 next_any=0',go(ACK+TA))
        self.assertIn('route_verified=1',go(ACK+TA))
        self.assertIn('ack_any=0 next_any=1',go(NEXT+TN))
        self.assertIn('route_verified=1',go(NEXT+TN))
        self.assertIn('entries=2 trials=2',go(ACK+TA+NEXT+TN))
    def test_invalid_mixed_and_unpaired_never_pass(self):
        for text in ('',ACK,TA,NEXT,TN,ACK+TN,NEXT+TA,
                     ACK+TA+NEXT+TA,ACK+ACK+TA+TA,
                     ACK.replace('y1cleared=1','y1cleared=0')+TA,
                     NEXT.replace('latch=1','latch=0')+TN,
                     ACK+TA+NEXT.replace('verified=1','verified=0')+TN):
            self.assertIn('route_verified=0',go(text),text)
    def test_private_guest_details_are_suppressed(self):
        s=go('private original guest data\n'+ACK+TA)
        self.assertNotIn('private original',s)
    def test_sample_completeness_flag(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'private'
            with p.open('wb') as f:
                f.write((ACK+TA).encode('ascii'))
                f.seek(WINDOW+80)
                f.write(b'\n')
            self.assertIn('sample_complete=0',inspect(p,124))
if __name__=='__main__':unittest.main()
