#!/usr/bin/env python3
"""V408 original-free authentic guest 50-cutpoint result and fail-closed gate."""
from pathlib import Path
import tempfile
import unittest
from analyze_v408_nand_cut50 import inspect
from audit_v408_nand_cut50 import verify

E=('V408_NAND_CUT50_STOP calls=50 owner=0 selected_return=1 parent_return=1\n')
T='V408_NAND_CUT50_TRIAL calls=50 kind=2 complete=1\n'
def run(data:str,rc:int=0)->tuple[str,bool]:
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'private.log'
        p.write_text(data,encoding='ascii')
        return inspect(p,rc),verify(p,rc)
class Tests(unittest.TestCase):
    def test_exact_original_native_50_horizon_required_for_all_trials(self):
        result,gate=run(('SECRET GAME PPC INSTRUCTION\n'+E+T)*16)
        self.assertTrue(gate)
        self.assertIn('entries=16 trials=16 max_calls=50',result)
        self.assertIn('owner_trials=0 cap50_trials=16',result)
        self.assertIn('full_progress=1 boot_verified=0',result)
        self.assertNotIn('SECRET',result)
    def test_incomplete_and_signal_do_not_count(self):
        for rc in (1,124,134):
            _,gate=run((E+T)*16,rc)
            self.assertFalse(gate)
        for count in (0,1,15,17):
            result,gate=run((E+T)*count)
            self.assertFalse(gate)
            self.assertNotIn('full_progress=1',result)
    def test_owned_exit_and_missing_origin_witness_do_not_claim_50(self):
        owned=E.replace('calls=50 owner=0','calls=22 owner=1')
        trial=T.replace('calls=50 kind=2','calls=22 kind=1')
        _,gate=run((owned+trial)*16)
        self.assertFalse(gate)
        altered=E.replace('selected_return=1','selected_return=0')
        _,gate=run((altered+T)*16)
        self.assertFalse(gate)
    def test_invalid_pairings_not_accepted(self):
        for sample in (E+T.replace('kind=2','kind=1'),E+T.replace('complete=1','complete=0'),
                       E+E+T,E+T+T,E,T):
            with self.subTest(length=len(sample)):
                result,gate=run((E+T)*15+sample)
                self.assertFalse(gate)
                self.assertIn('full_progress=0',result)
if __name__=='__main__':unittest.main()
