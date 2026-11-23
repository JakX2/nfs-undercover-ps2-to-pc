#!/usr/bin/env python3
"""V399 temporal pairing and original-free provenance checks."""
from pathlib import Path
import tempfile
import unittest
from analyze_v399_nand_return_order import inspect
from test_v398_nand_return_site_audit import E as E398
R='V399_NAND_RETURN_ORDER site=1 mapped=1 bctrl=1 isfs_after=1 parent_after=0 ordered=1 blr_verified=0\n'
T='V399_NAND_RETURN_TRIAL ordered=1 completed=1\n'
E=E398.replace('samples=0','samples=22').replace('site=0','site=1').replace(
    'mapped=0','mapped=1').replace('before_cap=0','before_cap=1')
def run(s:str,rc:int=0)->str:
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'private.log'
        p.write_text(s,encoding='ascii')
        return inspect(p,rc)
class Tests(unittest.TestCase):
    def test_full_natural_return_pc_then_isfs_origin_per_trial(self):
        text=run(('PROPRIETARY 0xdeadbeef\n'+E+R+T)*16)
        self.assertIn('entries=16 trials=16 site_trials=16',text)
        self.assertIn('mapped_trials=16 bctrl_trials=16 isfs_after_trials=16',text)
        self.assertIn('ordered_trials=16 lineage_verified=1 blr_verified=0',text)
        self.assertNotIn('PROPRIETARY',text)
    def test_unordered_and_unsampled_traces_fail(self):
        bad=(E+T,E+R,E+R+T+T,R+E+T,T+E+R,
             E398+R+T,
             E+R.replace('ordered=1','ordered=0')+T,
             E+R.replace('bctrl=1','bctrl=0')+T.replace('completed=1','completed=0'),
             E+R.replace('site=1','site=0')+T,
             E+R.replace('isfs_after=1','isfs_after=0')+T,
             E+R+T.replace('ordered=1','ordered=0'),
             (E+R+T)*17)
        for item in bad:
            with self.subTest(size=len(item)):
                self.assertIn('lineage_verified=0',run(item),item)
    def test_empty_diagnostic_allowed_but_not_return(self):
        r=R.replace('site=1','site=0').replace('mapped=1','mapped=0').replace(
            'bctrl=1','bctrl=0').replace('isfs_after=1','isfs_after=0').replace('ordered=1','ordered=0')
        t=T.replace('ordered=1','ordered=0')
        self.assertIn('lineage_verified=1 blr_verified=0',run(E398+r+t))
if __name__=="__main__":unittest.main()
