#!/usr/bin/env python3
"""Original-free V404 96-call owner evidence gate."""
import tempfile
import unittest
from pathlib import Path
from audit_v404_nand_extended import verify
from test_v404_nand_extended_audit import E96,T96,E21,T21

def run(data:str,rc:int=0)->bool:
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'owner-private.log'
        p.write_text(data,encoding='ascii')
        return verify(p,rc)

class Tests(unittest.TestCase):
    def test_all_16_original_calls_beyond_48_required(self):
        self.assertTrue(run((E96+T96)*16))
        self.assertFalse(run((E96+T96)*15))
        self.assertFalse(run((E96+T96)*17))
        for rc in (1,124,126,134):
            self.assertFalse(run((E96+T96)*16,rc))
    def test_natural_owner_exit_is_not_96_call_verification(self):
        self.assertFalse(run((E21+T21)*16))
    def test_guest_return_diagnostics_missing_or_corrupt(self):
        for invalid in (
            E96+T96.replace('complete=1','complete=0'),
            E96+T96.replace('kind=2','kind=1'),
            E96.replace('parent_return=1','parent_return=0')+T96,
            E96+T96+T96,
            E96+E96+T96,
            E96,
        ):
            with self.subTest(size=len(invalid)):
                self.assertFalse(run((E96+T96)*15+invalid))
    def test_no_private_addresses_leak(self):
        self.assertTrue(run(('ORIGINAL GUEST 0x80519bcc\n'+E96+T96)*16))
if __name__=='__main__':
    unittest.main()
