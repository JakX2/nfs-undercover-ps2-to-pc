#!/usr/bin/env python3
"""V377 fixed-shape privacy-preserving original NAND handler audit."""
import tempfile
import unittest
from pathlib import Path
from analyze_v377_nand_vector_handler import inspect
from diagnose_v299_native_log import WINDOW

def generate(v=1,h=1,t=1):
    return (
        f'V377_NAND_VECTOR_ENTRY saved={v} regs=1 bytes=1 masked=1 pending=1\n'
        f'V377_NAND_HANDLER_ENTRY vector={h} index=1 frame=1 saved=1 masked=1 y1=1 advanced=1\n'
        f'V377_NAND_HANDLER_TRIAL stopped={t} vector=1 handler=1 completed=1\n'
    )
def go(s,rc=0):
    with tempfile.TemporaryDirectory() as tmp:
        path=Path(tmp)/'owner-game-proprietary.log'
        path.write_text(s,encoding='utf-8')
        return inspect(path,rc)
class Tests(unittest.TestCase):
    def test_authenticated_original_chain_not_exposed(self):
        result=go('sensitive caller pointer omitted\n'+generate())
        self.assertIn('vectors=1 handlers=1 trials=1',result)
        self.assertIn('chain_verified=1',result)
        self.assertNotIn('sensitive caller',result)
        self.assertNotIn('proprietary',result)
    def test_missing_or_invalid_evidence_never_proves_handler(self):
        for raw in (
            '',generate()[:-1].replace('completed=1','completed=0')+'\n',
            generate(v=0),generate(h=0),generate(t=0),
            'prefix '+generate(),generate().split('\n',1)[0]+'\n'
        ):
            self.assertIn('chain_verified=0',go(raw),raw)
    def test_mixed_good_bad_or_out_of_order_never_proves_chain(self):
        good=generate()
        wrong=generate(h=0)
        for raw in (
            good+wrong,
            wrong+good,
            good+generate(v=0),
            good+generate(t=0),
            generate().split('\n')[0]+'\n'+good,
            good+generate().split('\n')[1]+'\n',
            good+generate().split('\n')[2]+'\n',
            generate().split('\n')[0]+'\n'+
              generate().split('\n')[0]+'\n'
        ):
            self.assertIn('chain_verified=0',go(raw),raw)
    def test_bounded_logging_and_truncation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'private.log'
            with path.open('wb') as f:
                f.write(generate().encode('ascii'))
                f.seek(WINDOW+80)
                f.write(b'\n')
            result=inspect(path,124)
            self.assertIn('sample_complete=0',result)
            self.assertIn('chain_verified=1',result)
if __name__=='__main__':
    unittest.main()
