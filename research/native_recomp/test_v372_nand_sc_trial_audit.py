#!/usr/bin/env python3
"""Original-free V372 post-V153 census safety and classifier tests."""
import tempfile
import unittest
from pathlib import Path
from analyze_v372_nand_sc_trial import inspect
from diagnose_v299_native_log import WINDOW

def run(contents:str,rc:int=134)->str:
    with tempfile.TemporaryDirectory() as root:
        path=Path(root)/'private.log'
        path.write_text(contents,encoding='utf-8')
        return inspect(path,rc)

class Tests(unittest.TestCase):
    def test_queued_reply_survives_original_flag_clear(self):
        result=run('private-secret\nV372_NAND_SC_TRIAL phase=1 sc_bridge=0 queued=1 '
                   'y1=0 y2=0 flag=0 irq=0 ee=0\n')
        self.assertIn('samples=1 bridge_any=0 queued_any=1 y1_any=0 y2_any=0 '
                      'flag_any=0 irq_any=0 ee_any=0',result)
        self.assertNotIn('private-secret',result)
        self.assertNotIn('private.log',result)

    def test_reports_later_y1_without_claiming_guest_handler_completed(self):
        result=run('V372_NAND_SC_TRIAL phase=1 sc_bridge=1 queued=0 '
                   'y1=1 y2=0 flag=1 irq=1 ee=1\n')
        self.assertIn('samples=1 bridge_any=1 queued_any=0 y1_any=1',result)
        self.assertIn('flag_any=1 irq_any=1 ee_any=1',result)
        self.assertNotIn('completed=',result)

    def test_invalid_prefix_and_bad_values_not_counted(self):
        result=run('extra V372_NAND_SC_TRIAL phase=1 sc_bridge=0 queued=1 y1=0 y2=0 flag=0 irq=0 ee=0\n'
                   'V372_NAND_SC_TRIAL phase=0 sc_bridge=0 queued=1 y1=0 y2=0 flag=0 irq=0 ee=0\n'
                   'V372_NAND_SC_TRIAL phase=1 sc_bridge=0 queued=2 y1=0 y2=0 flag=0 irq=0 ee=0\n')
        self.assertIn('samples=0',result)

    def test_tail_truncation_is_visible_and_exit_checked(self):
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/'private.log'
            with path.open('wb') as f:
                f.write(b'V372_NAND_SC_TRIAL phase=1 sc_bridge=0 queued=1 y1=0 y2=0 flag=0 irq=0 ee=0\n')
                f.seek(WINDOW+200)
                f.write(b'\nend\n')
            self.assertIn('sample_complete=0 samples=1',inspect(path,124))
        for code in (-1,256):
            with self.assertRaises(ValueError):
                run('',code)

if __name__=='__main__':
    unittest.main()
