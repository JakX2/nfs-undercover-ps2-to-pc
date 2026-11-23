#!/usr/bin/env python3
"""V393 strict original-free post-NAND ACK guest-call censuses."""
import tempfile
import unittest
from pathlib import Path
from analyze_v393_nand_guest_next import inspect
from diagnose_v299_native_log import WINDOW
E='V393_NAND_NEXT_CALL guest=1 clear=1 registered=1 masked=1 reply=1 clearctx=0 setctx=1 cache=0 isfs=0\n'
T='V393_NAND_NEXT_TRIAL first=1 next=1 completed=1\n'
def test(raw,rc=0):
    with tempfile.TemporaryDirectory() as tmp:
        file=Path(tmp)/'proprietary.log'
        file.write_text(raw,encoding='utf-8')
        return inspect(file,rc)
class Tests(unittest.TestCase):
    def test_real_original_call_classification_sanitized(self):
        out=test('hidden registers\n'+E+T)
        self.assertIn('entries=1 trials=1 reply_any=1',out)
        self.assertIn('setctx_any=1 cache_any=0 isfs_any=0 next_verified=1',out)
        self.assertNotIn('hidden registers',out)
    def test_unknown_real_call_does_not_require_callback(self):
        e=E.replace('reply=1','reply=0').replace('setctx=1','setctx=0')
        self.assertIn('next_verified=1',test(e+T))
    def test_unpaired_mixed_negative_not_verified(self):
        for raw in ('',E,T,E+E+T,T+E+T,E+T+T,
                    E.replace('guest=1','guest=0')+T,
                    E.replace('clear=1','clear=0')+T,
                    E+T+E+T.replace('completed=1','completed=0')):
            self.assertIn('next_verified=0',test(raw),raw)
    def test_large_log_bounded_sample(self):
        with tempfile.TemporaryDirectory() as tmp:
            file=Path(tmp)/'hidden-private.log'
            with file.open('wb') as f:
                f.write((E+T).encode('ascii'))
                f.seek(WINDOW+96)
                f.write(b'\n')
            self.assertIn('sample_complete=0',inspect(file,124))
if __name__=="__main__":unittest.main()
