#!/usr/bin/env python3
"""V391 post-ACK bounded trace audit rejects mixed/invalid evidence."""
import tempfile
import unittest
from pathlib import Path
from analyze_v391_nand_post_ack_next import inspect
from diagnose_v299_native_log import WINDOW
E='V391_NAND_POST_ACK_EVENT kind=1 verified=1 owner=1 cache=0 context=1 callback=0 cap=0\n'
T='V391_NAND_POST_ACK_TRIAL kind=1 stopped=1 completed=1\n'
def run(raw,rc=0):
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'owner-private.log'
        p.write_text(raw,encoding='utf-8')
        return inspect(p,rc)
class Tests(unittest.TestCase):
    def test_genuine_original_reply_context_successor_redacted(self):
        result=run('private game PPU source\n'+E+T)
        self.assertIn('entries=1 trials=1 owner_any=1 cap_any=0',result)
        self.assertIn('context_any=1 callback_any=0 next_verified=1',result)
        self.assertNotIn('private game',result)
        self.assertNotIn('owner-private',result)
    def test_legitimate_bounded_unknown_is_not_callback(self):
        e='V391_NAND_POST_ACK_EVENT kind=2 verified=1 owner=0 cache=0 context=0 callback=0 cap=1\n'
        t='V391_NAND_POST_ACK_TRIAL kind=2 stopped=1 completed=1\n'
        res=run(e+t)
        self.assertIn('owner_any=0 cap_any=1',res)
        self.assertIn('next_verified=1',res)
    def test_malformed_wrong_order_or_mixed_result_never_proves(self):
        for raw in (
            '',E,T,T+E+T,E+E+T,E+T+T,
            E.replace('verified=1','verified=0')+T,
            E.replace('owner=1','owner=0')+T,
            E+T+E.replace('cap=0','cap=1')+T,
            E+T+E+T.replace('completed=1','completed=0')
        ):self.assertIn('next_verified=0',run(raw),raw)
    def test_large_log_incomplete(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'owner-private.log'
            with p.open('wb') as f:
                f.write((E+T).encode('ascii'))
                f.seek(WINDOW+64)
                f.write(b'\n')
            self.assertIn('sample_complete=0',inspect(p,124))
if __name__=="__main__":unittest.main()
