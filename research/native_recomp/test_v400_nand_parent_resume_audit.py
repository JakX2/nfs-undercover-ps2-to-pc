#!/usr/bin/env python3
"""V400 original-free temporal parent return analyzer tests."""
from pathlib import Path
import tempfile
import unittest
from analyze_v400_nand_parent_resume import inspect
from test_v399_nand_return_order_audit import E as E398,R as E399
E='V400_NAND_PARENT_RESUME site=1 mapped=1 linked=1 selected_first=1 parent_after=1 ordered=1 blr_verified=0\n'
T='V400_NAND_PARENT_TRIAL ordered=1 completed=1\n'
def run(raw:str,rc:int=0)->str:
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'private-owner.log'
        path.write_text(raw,encoding='ascii')
        return inspect(path,rc)
class Tests(unittest.TestCase):
    def test_sixteen_guest_parent_continuations_with_no_blr_claim(self):
        result=run(('SECRET ORIGINAL GUEST DATA\n'+E398+E399+E+T)*16)
        self.assertIn('entries=16 trials=16 site_trials=16 mapped_trials=16',result)
        self.assertIn('linked_trials=16 selected_first_trials=16',result)
        self.assertIn('ordered_trials=16 lineage_verified=1 blr_verified=0',result)
        self.assertNotIn('SECRET ORIGINAL',result)
    def test_bad_order_missing_data_and_opcode_claim_rejected(self):
        for bad in (
            E398+E399+T,E398+E+T,E399+E+T,
            E398+E399+E+E+T,E398+E399+E+T+T,
            E398+E399+E.replace('ordered=1','ordered=0')+T,
            E398+E399+E.replace('selected_first=1','selected_first=0')+T,
            E398+E399+E.replace('mapped=1','mapped=0')+T,
            E398+E399+E.replace('site=1','site=0')+T,
            E398+E399+E.replace('blr_verified=0','blr_verified=1')+T,
            E398+E399+E+T.replace('completed=1','completed=0'),
            (E398+E399+E+T)*17,
        ):
            with self.subTest(size=len(bad)):
                self.assertIn('lineage_verified=0',run(bad))
    def test_zero_parent_pc_observation_is_accurately_classified(self):
        none=E.replace('site=1','site=0').replace('mapped=1','mapped=0').replace(
            'linked=1','linked=0').replace('selected_first=1','selected_first=0').replace(
            'parent_after=1','parent_after=0').replace('ordered=1','ordered=0')
        trial=T.replace('ordered=1','ordered=0')
        self.assertIn('lineage_verified=1 blr_verified=0',run(E398+E399+none+trial))
if __name__=="__main__":unittest.main()
