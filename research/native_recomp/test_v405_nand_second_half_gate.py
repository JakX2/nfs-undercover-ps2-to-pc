#!/usr/bin/env python3
"""Original-free V405 standalone owner 16x48 successor-region gate."""
from pathlib import Path
import tempfile
import unittest
from audit_v405_nand_second_half import verify
from test_v404_nand_extended_audit import E96,T96
from test_v405_nand_second_half_audit import E,T
def sample(e:str=E,t:str=T)->str:
    return E96+e+T96+t
def run(data:str,rc:int=0):
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'private.log'
        p.write_text(data,encoding='ascii')
        return verify(p,rc)
class Tests(unittest.TestCase):
    def test_full_original_96_and_second_half_required(self):
        self.assertEqual(run(sample()*16),(True,1,1,0,0))
        self.assertEqual(run(sample()*15),(False,0,0,0,0))
        self.assertEqual(run(sample()*17),(False,0,0,0,0))
        for rc in (1,124,134):
            self.assertEqual(run(sample()*16,rc),(False,0,0,0,0))
    def test_all_original_second_half_calls_still_need_correct_partition(self):
        for invalid in (
            E.replace('isfs=12','isfs=11'),
            E.replace('other=16','other=17'),
            E.replace('tail_calls=48','tail_calls=47'),
            E.replace('nand=0','nand=49'),
        ):
            with self.subTest(size=len(invalid)):
                self.assertFalse(run(sample()*15+sample(invalid))[0])
        self.assertFalse(run(sample()*15+sample(t=T.replace('completed=1','completed=0')))[0])
    def test_counts_never_leak_private_original_words(self):
        self.assertTrue(run(('PRIVATE DATA 0x81234567\n'+sample())*16)[0])
if __name__=='__main__':
    unittest.main()
