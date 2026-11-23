#!/usr/bin/env python3
"""Original-free V385 live ARMMSG returned value evidence auditor tests."""
import tempfile
import unittest
from pathlib import Path
from analyze_v385_nand_armmsg_scope import inspect
from diagnose_v299_native_log import WINDOW
GOOD='V385_NAND_ARMMSG_MIRROR coherent=1 y1=1\n'
def run(s,rc=0):
    with tempfile.TemporaryDirectory() as root:
        p=Path(root)/'private-source-binary.log'
        p.write_text(s,encoding='utf-8')
        return inspect(p,rc)
class Tests(unittest.TestCase):
    def test_one_genuine_coherent_read(self):
        result=run('proprietary register 0xdeadbeef\n'+GOOD)
        self.assertIn('samples=1 coherent_any=1 y1_any=1 mailbox_verified=1',result)
        self.assertNotIn('0xdeadbeef',result)
        self.assertNotIn('private-source-binary',result)
    def test_missing_or_mixed_false_never_passes(self):
        for s in ('',GOOD+'V385_NAND_ARMMSG_MIRROR coherent=0 y1=1\n',
                  'V385_NAND_ARMMSG_MIRROR coherent=0 y1=1\n'+GOOD,
                  GOOD+'V385_NAND_ARMMSG_MIRROR coherent=1 y1=0\n'):
            self.assertIn('mailbox_verified=0',run(s),s)
    def test_truncated_log_reported(self):
        with tempfile.TemporaryDirectory() as root:
            p=Path(root)/'private.log'
            with p.open('wb') as f:
                f.write(GOOD.encode())
                f.seek(WINDOW+80)
                f.write(b'\n')
            result=inspect(p,124)
            self.assertIn('sample_complete=0',result)
            self.assertIn('mailbox_verified=1',result)
if __name__=='__main__':
    unittest.main()
