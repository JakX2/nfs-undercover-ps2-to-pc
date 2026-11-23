#!/usr/bin/env python3
"""V374 native reply-yield census: original-free safety checks."""
import tempfile
import unittest
from pathlib import Path
from analyze_v374_nand_ios_reply import inspect
from diagnose_v299_native_log import WINDOW

def line(n:int,*,yclear=1,flagclear=1,irq_before=0,
         fired=1,pump=2,y1=1,queued=0,irq_after=1,eligible=0)->str:
    return (f'V374_NAND_REPLY_GATE n={n} yclear={yclear} flagclear={flagclear} '
            f'irq_before={irq_before} fired={fired} pump={pump} y1={y1} '
            f'queued={queued} irq_after={irq_after} eligible={eligible}\n')

def run(content:str,rc:int=0)->str:
    with tempfile.TemporaryDirectory() as directory:
        path=Path(directory)/'secret-owner.log'
        path.write_text(content,encoding='utf-8')
        return inspect(path,rc)

class Tests(unittest.TestCase):
    def test_real_reply_publication_without_guest_handler_claim(self):
        output=run('private owner data\n'+line(1,eligible=1))
        self.assertIn('samples=1 ready_any=1 blocked_y_any=0',output)
        self.assertIn('serviced_any=1 replied_any=1 y1_any=1 queued_any=0',output)
        self.assertIn('irq_any=1 eligible_any=1',output)
        self.assertNotIn('private owner data',output)
        self.assertNotIn('secret-owner.log',output)
        self.assertNotIn('handler_completed',output)

    def test_no_early_reply_and_hardware_flag_barrier(self):
        output=run(line(1,yclear=0,flagclear=0,irq_before=1,
                        fired=0,pump=0,y1=0,queued=1,irq_after=1))
        self.assertIn('samples=1 ready_any=0 blocked_y_any=1',output)
        self.assertIn('blocked_flag_any=1 serviced_any=0 replied_any=0',output)

    def test_invalid_claims_and_missing_markers_are_not_counted(self):
        self.assertIn('samples=0',run('prefix '+line(1)))
        self.assertIn('samples=0',run(line(2)))
        self.assertIn('samples=0',run(line(1,yclear=0,fired=1)))
        self.assertIn('samples=0',run(line(1,fired=0,pump=2)))
        self.assertIn('samples=0',run(line(1,eligible=1,irq_after=0)))
        self.assertIn('samples=1',run(line(1)+line(3)))
        self.assertIn('samples=0',run(line(17)))
        for bad in (-1,256):
            with self.assertRaises(ValueError):
                run('',bad)

    def test_truncation_is_visible_and_not_success(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'secret-owner.log'
            with path.open('wb') as stream:
                stream.write(line(1).encode('ascii'))
                stream.seek(WINDOW+200)
                stream.write(b'\nend\n')
            self.assertIn('sample_complete=0 samples=1',inspect(path,124))

if __name__=='__main__':
    unittest.main()
