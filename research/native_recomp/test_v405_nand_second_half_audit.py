#!/usr/bin/env python3
"""Original-free V405 post-48 call origin and pair-order audit cases."""
from pathlib import Path
import tempfile
import unittest
from analyze_v405_nand_second_half import inspect

E=('V405_NAND_SECOND_HALF tail_calls=48 selected=0 isfs=12 '
   'parent=20 other=16 nand=0 cache=0\n')
T='V405_NAND_SECOND_TRIAL tail_calls=48 completed=1\n'
def run(data:str,rc:int=0)->str:
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'owner.log'
        p.write_text(data,encoding='ascii')
        return inspect(p,rc)
class Tests(unittest.TestCase):
    def test_full_post_48_origin_histogram(self):
        s=run(('PRIVATE GAME 0x81234567\n'+E+T)*16)
        self.assertIn('entries=16 trials=16 max_tail=48 full48_trials=16',s)
        self.assertIn('isfs_total=192 parent_total=320 other_total=256',s)
        self.assertIn('lineage_verified=1 boot_verified=0',s)
        self.assertNotIn('PRIVATE GAME',s)
    def test_partial_bounded_data_is_diagnostic(self):
        e='V405_NAND_SECOND_HALF tail_calls=0 selected=0 isfs=0 parent=0 other=0 nand=0 cache=0\n'
        t='V405_NAND_SECOND_TRIAL tail_calls=0 completed=1\n'
        self.assertIn('lineage_verified=1',run(e+t))
        self.assertIn('full48_trials=0',run(e+t))
    def test_malformed_counts_and_unpaired_records(self):
        for data in (
            E,E+T+T,E+E+T,T+E+T,
            E.replace('other=16','other=17')+T,
            E.replace('nand=0','nand=49')+T,
            E.replace('cache=0','cache=49')+T,
            E.replace('tail_calls=48','tail_calls=49')+T,
            E+T.replace('tail_calls=48','tail_calls=47'),
            E+T.replace('completed=1','completed=0'),
            (E+T)*17
        ):
            with self.subTest(size=len(data)):
                self.assertIn('lineage_verified=0',run(data))
if __name__=='__main__':
    unittest.main()
