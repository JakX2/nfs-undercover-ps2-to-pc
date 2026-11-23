#!/usr/bin/env python3
"""V397 sanitized guest LR lineage log scanner regression tests."""
from pathlib import Path
import tempfile
import unittest
from analyze_v397_nand_callback_lineage import inspect
E=('V397_NAND_ORIGINS mask=10 last=4 calls=24 selected_any=0 '
   'isfs_any=1 parent_any=0 other_any=1 same_lr_any=0\n')
T='V397_NAND_ORIGINS_TRIAL completed=1 stopped=1\n'
def run(raw:str,rc:int=0)->str:
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'owner-private.log'
        p.write_text(raw,encoding='ascii')
        return inspect(p,rc)
class Tests(unittest.TestCase):
    def test_full_bounded_lineage_without_return_claim(self):
        s=run(('PRIVATE GUEST CODE NOT EXPORTED\n'+E+T)*16)
        self.assertIn('entries=16 trials=16 mask=10 full_cap_all=1',s)
        self.assertIn('selected_any=0 isfs_any=1',s)
        self.assertIn('lineage_verified=1 return_verified=0',s)
        self.assertNotIn('PRIVATE GUEST',s)
    def test_malformed_and_unpaired_rejected(self):
        for sample in ('',E,T,E+E+T,T+E+T,
                       E.replace('mask=10','mask=8')+T,
                       E.replace('isfs_any=1','isfs_any=0')+T,
                       E.replace('calls=24','calls=25')+T,
                       E+T+T,E+T.replace('completed=1','completed=0'),(E+T)*17):
            with self.subTest(size=len(sample)):
                self.assertIn('lineage_verified=0',run(sample),sample)
    def test_one_pair_not_a_return(self):
        self.assertIn('lineage_verified=1 return_verified=0',run(E+T))
        self.assertIn('lineage_verified=1 return_verified=0',run(E+T,134))
if __name__=='__main__':unittest.main()
