#!/usr/bin/env python3
"""V376 original-free audit bounds and original code privacy tests."""
import tempfile
import unittest
from pathlib import Path
from analyze_v376_nand_y1_vector import inspect
from diagnose_v299_native_log import WINDOW

def sample(n,*,safe=1,installed=1,entered=1,saved=1,
           regs=1,masked=1,queued=0):
    return (f'V376_NAND_VECTOR n={n} y1=1 safe={safe} installed={installed} '
            f'entered={entered} saved={saved} regs={regs} '
            f'irq_masked={masked} queued={queued}\n')

def check(content,rc=0):
    with tempfile.TemporaryDirectory() as p:
        file=Path(p)/'private-owner-dol-raw.log'
        file.write_text(content,encoding='utf-8')
        return inspect(file,rc)

class Tests(unittest.TestCase):
    def test_first_authentic_entry_and_no_handler_claim(self):
        out=check('raw private data\n'+sample(1))
        self.assertIn('samples=1 eligible_any=1 safe_any=1',out)
        self.assertIn('entered_any=1 saved_any=1 regs_any=1 masked_any=1',out)
        self.assertIn('handler_executed=0',out)
        self.assertNotIn('raw private data',out)
        self.assertNotIn('private-owner-dol-raw',out)

    def test_incomplete_vector_never_claims_entry(self):
        out=check(sample(1,safe=0,installed=0,entered=0,saved=0,
                         regs=1,masked=0,queued=1))
        self.assertIn('samples=1',out)
        self.assertIn('entered_any=0',out)
        self.assertIn('queued_any=1',out)

    def test_invalid_sequence_cannot_fake_entry(self):
        for content in (
            'prefix '+sample(1),
            sample(2),
            sample(1,safe=0),
            sample(1,installed=0),
            sample(1,saved=0),
            sample(1,regs=0),
            sample(1,masked=0),
            sample(17)
        ):
            self.assertIn('samples=0',check(content),content)
        self.assertIn('samples=1',check(sample(1)+sample(3)))

    def test_truncation_marks_sample_incomplete(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'private.log'
            with path.open('wb') as out:
                out.write(sample(1).encode('ascii'))
                out.seek(WINDOW+200)
                out.write(b'\nend\n')
            self.assertIn('sample_complete=0 samples=1',inspect(path,124))

if __name__=='__main__':
    unittest.main()
