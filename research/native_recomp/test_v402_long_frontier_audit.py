#!/usr/bin/env python3
"""V402 extended native AOT outcome tests: truthful successes and early aborts."""
from pathlib import Path
import tempfile
import unittest
from analyze_v402_long_frontier import inspect
E48=('V402_NAND_LONG_STOP calls=48 owner=0 selected_return=1 '
     'parent_return=1\n')
T48='V402_NAND_LONG_TRIAL calls=48 kind=2 complete=1\n'
E12=('V402_NAND_LONG_STOP calls=12 owner=1 selected_return=1 '
     'parent_return=1\n')
T12='V402_NAND_LONG_TRIAL calls=12 kind=1 complete=1\n'
def run(raw:str,rc:int=0)->str:
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'private.log'
        p.write_text(raw,encoding='ascii')
        return inspect(p,rc)
class Tests(unittest.TestCase):
    def test_full_original_guest_horizon_all_sixteen(self):
        text=run(('PRIVATE 0xcafefeed\n'+E48+T48)*16)
        self.assertIn('rc=0 kind=zero',text)
        self.assertIn('entries=16 trials=16 max_calls=48',text)
        self.assertIn('owner_trials=0 cap48_trials=16',text)
        self.assertIn('selected_return_trials=16 parent_return_trials=16',text)
        self.assertIn('full_progress=1 boot_verified=0',text)
        self.assertNotIn('PRIVATE',text)
    def test_natural_early_owned_return_is_a_valid_bounded_result(self):
        text=run((E12+T12)*16)
        self.assertIn('owner_trials=16 cap48_trials=0',text)
        self.assertIn('full_progress=1 boot_verified=0',text)
    def test_early_native_abort_is_diagnostic_not_false_success(self):
        for rc in (1,124,134,126):
            result=run((E48+T48)*8,rc)
            self.assertIn('entries=8 trials=8',result)
            self.assertIn('full_progress=0 boot_verified=0',result)
        self.assertIn('entries=0 trials=0',run('',134))
        self.assertIn('full_progress=0',run('private abort\n',134))
    def test_malformed_or_unpaired_rejected(self):
        for event in (
            E48+T48.replace('kind=2','kind=1'),
            E48+T48.replace('calls=48','calls=47'),
            E48+T48.replace('complete=1','complete=0'),
            E48.replace('parent_return=1','parent_return=0')+T48,
            E48.replace('owner=0','owner=1')+T48,
            E12.replace('owner=1','owner=0')+T12,
            E48+T48+T48,E48+E48+T48,
            (E48+T48)*17,
        ):
            with self.subTest(size=len(event)):
                self.assertIn('full_progress=0',run(event),event)
if __name__=='__main__':unittest.main()
