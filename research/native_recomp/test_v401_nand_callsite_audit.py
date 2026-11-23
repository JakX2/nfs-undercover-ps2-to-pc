#!/usr/bin/env python3
"""V401 sanitized original guest opcode classification scanner tests."""
from pathlib import Path
import tempfile
import unittest
from analyze_v401_nand_callsite import inspect
from test_v399_nand_return_order_audit import E as E398
E='V401_NAND_CALLSITE mapped=1 kind=1 direct_match=1 selected_site=1 blr_verified=0\n'
T='V401_NAND_CALLSITE_TRIAL kind=1 completed=1\n'
def run(raw:str,rc:int=0)->str:
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'original.log'
        p.write_text(raw,encoding='ascii')
        return inspect(p,rc)
class Tests(unittest.TestCase):
    def test_sixteen_original_bl_calls_target_matching_native_guest(self):
        s=run(('private original 0xff33cc11\n'+E398+E+T)*16)
        self.assertIn('entries=16 trials=16 kind0=0 kind1=16',s)
        self.assertIn('kind5=0 site_trials=16 direct_match_trials=16',s)
        self.assertIn('classified=1 blr_verified=0',s)
        self.assertNotIn('private original',s)
    def test_missing_duplicated_or_false_link_proofs_fail_closed(self):
        invalid=(E398+E,E+T,T+E,E398+E+T+T,E398+E+E+T,
                 E398+E.replace('kind=1','kind=0')+T,
                 E398+E.replace('mapped=1','mapped=0')+T,
                 E398+E.replace('selected_site=1','selected_site=0')+T,
                 E398+E.replace('kind=1','kind=3')+T,
                 E398+E.replace('blr_verified=0','blr_verified=1')+T,
                 E398+E+T.replace('completed=1','completed=0'),
                 (E398+E+T)*17)
        for x in invalid:
            with self.subTest(len=len(x)):
                self.assertIn('classified=0',run(x))
    def test_zero_observation_is_not_reported_as_a_branch(self):
        from test_v398_nand_return_site_audit import E as E398_EMPTY
        notseen=E.replace('mapped=1','mapped=0').replace('kind=1','kind=0').replace(
            'direct_match=1','direct_match=0').replace('selected_site=1','selected_site=0')
        trial=T.replace('kind=1','kind=0')
        self.assertIn('classified=1 blr_verified=0',run(E398_EMPTY+notseen+trial))
if __name__=="__main__":unittest.main()
