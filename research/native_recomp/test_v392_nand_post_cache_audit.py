#!/usr/bin/env python3
"""V392 public-only post-cache evidence privacy and strict ordering tests."""
import tempfile
import unittest
from pathlib import Path
from analyze_v392_nand_post_cache import inspect
from diagnose_v299_native_log import WINDOW
E='V392_NAND_POST_CACHE_EVENT kind=1 verified=1 owner=1 cache=0 context=1 callback=0 bounded=0 caches=2\n'
T='V392_NAND_POST_CACHE_TRIAL kind=1 stopped=1 completed=1\n'
def run(raw,rc=0):
    with tempfile.TemporaryDirectory() as tmp:
        p=Path(tmp)/'private-wii-owner-original.log'
        p.write_text(raw,encoding='utf-8')
        return inspect(p,rc)
class Tests(unittest.TestCase):
    def test_legitimate_original_context_callee_without_private_data(self):
        res=run('private powerpc context words\n'+E+T)
        self.assertIn('entries=1 trials=1 owner_any=1 bounded_any=0',res)
        self.assertIn('cache_any=1 context_any=1 callback_any=0 next_verified=1',res)
        self.assertNotIn('private powerpc',res)
    def test_bounded_cache_only_does_not_claim_context(self):
        e='V392_NAND_POST_CACHE_EVENT kind=2 verified=1 owner=0 cache=1 context=0 callback=0 bounded=1 caches=24\n'
        t='V392_NAND_POST_CACHE_TRIAL kind=2 stopped=1 completed=1\n'
        self.assertIn('bounded_any=1 cache_any=1 context_any=0 callback_any=0 next_verified=1',run(e+t))
    def test_missing_invalid_unordered_or_mixed_fails(self):
        for raw in (
            '',E,T,T+E+T,E+E+T,E+T+T,
            E.replace('verified=1','verified=0')+T,
            E.replace('kind=1','kind=2')+T,
            E+T+E.replace('context=1','context=0').replace('owner=1','owner=0')+T,
            E+T+E+T.replace('completed=1','completed=0')
        ):self.assertIn('next_verified=0',run(raw),raw)
    def test_incomplete_log_sample_flag(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'private.log'
            with p.open('wb') as f:
                f.write((E+T).encode('ascii'))
                f.seek(WINDOW+100)
                f.write(b'\n')
            self.assertIn('sample_complete=0',inspect(p,124))
if __name__=="__main__":unittest.main()
