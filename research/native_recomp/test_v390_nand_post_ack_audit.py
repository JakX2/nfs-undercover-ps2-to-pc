#!/usr/bin/env python3
"""Original-free V390 post-ACK bounded audit, no owner-private disclosure."""
import tempfile
import unittest
from pathlib import Path
from analyze_v390_nand_post_ack import inspect
from diagnose_v299_native_log import WINDOW
E='V390_NAND_POST_ACK guest=1 clear=1 registered=1 masked=1 cache=1 context=0\n'
T='V390_NAND_POST_ACK_TRIAL flag=1 next=1 completed=1\n'
def run(data,rc=0):
    with tempfile.TemporaryDirectory() as directory:
        p=Path(directory)/'private-native-owner.log'
        p.write_text(data,encoding='utf-8')
        return inspect(p,rc)
class Tests(unittest.TestCase):
    def test_verified_original_cache_classification_and_redaction(self):
        result=run('secret guest program counter and binary\n'+E+T)
        self.assertIn('entries=1 trials=1 cache_any=1 context_any=0 next_verified=1',result)
        self.assertNotIn('secret guest',result)
        self.assertNotIn('private-native',result)
    def test_unknown_original_callee_is_not_invented(self):
        result=run(E.replace('cache=1','cache=0')+T)
        self.assertIn('cache_any=0',result)
        self.assertIn('next_verified=1',result)
    def test_malformed_or_mixed_trace_not_verified(self):
        for raw in ('',E,T,T+E+T,E+E+T,E+T+T,
                    E.replace('clear=1','clear=0')+T,
                    E+T+E.replace('masked=1','masked=0')+T,
                    E+T+E+T.replace('completed=1','completed=0')):
            self.assertIn('next_verified=0',run(raw),raw)
    def test_truncated_log_disclosed(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'private.log'
            with p.open('wb') as f:
                f.write((E+T).encode('ascii'))
                f.seek(WINDOW+96)
                f.write(b'\n')
            result=inspect(p,124)
            self.assertIn('sample_complete=0',result)
            self.assertIn('next_verified=1',result)
if __name__=="__main__":unittest.main()
