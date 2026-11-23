#!/usr/bin/env python3
"""Original-free V404 96-call verified / incomplete / malformed results."""
from pathlib import Path
import tempfile
import unittest
from analyze_v404_nand_extended import inspect
E96=('V404_NAND_EXTENDED_STOP calls=96 owner=0 selected_return=1 '
     'parent_return=1\n')
T96='V404_NAND_EXTENDED_TRIAL calls=96 kind=2 complete=1\n'
E21=('V404_NAND_EXTENDED_STOP calls=21 owner=1 selected_return=1 '
     'parent_return=1\n')
T21='V404_NAND_EXTENDED_TRIAL calls=21 kind=1 complete=1\n'

def run(data:str,rc:int=0)->str:
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'private-owner.log'
        path.write_text(data,encoding='ascii')
        return inspect(path,rc)

class Tests(unittest.TestCase):
    def test_full_96_call_original_guest_horizon(self):
        result=run(('PRIVATE DATA 0x8000caf0\n'+E96+T96)*16)
        self.assertIn('rc=0 kind=zero',result)
        self.assertIn('entries=16 trials=16 max_calls=96',result)
        self.assertIn('owner_trials=0 cap96_trials=16',result)
        self.assertIn('selected_return_trials=16 parent_return_trials=16',result)
        self.assertIn('full_progress=1 boot_verified=0',result)
        self.assertNotIn('PRIVATE DATA',result)
    def test_early_natural_owned_completion_is_distinct(self):
        result=run((E21+T21)*16)
        self.assertIn('owner_trials=16 cap96_trials=0',result)
        self.assertIn('full_progress=1 boot_verified=0',result)
    def test_failed_and_aborted_runs_are_not_success(self):
        for rc in (1,124,126,134):
            result=run((E96+T96)*8,rc)
            self.assertIn('entries=8 trials=8',result)
            self.assertIn('full_progress=0 boot_verified=0',result)
        self.assertIn('entries=0 trials=0',run('',134))
    def test_strict_pairing_and_caps(self):
        bad=(
            E96+T96.replace('kind=2','kind=1'),
            E96+T96.replace('calls=96','calls=95'),
            E96+T96.replace('complete=1','complete=0'),
            E96.replace('parent_return=1','parent_return=0')+T96,
            E96.replace('owner=0','owner=1')+T96,
            E21.replace('owner=1','owner=0')+T21,
            E96+T96+T96,E96+E96+T96,
            (E96+T96)*17
        )
        for case in bad:
            with self.subTest(size=len(case)):
                self.assertIn('full_progress=0',run(case))
if __name__=='__main__':unittest.main()
