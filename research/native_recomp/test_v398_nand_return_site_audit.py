#!/usr/bin/env python3
"""V398 bounded original-free return PC census tests."""
from pathlib import Path
import tempfile
import unittest
from analyze_v398_nand_return_site import inspect
E='V398_NAND_RETURN_PC samples=0 site=0 mapped=0 before_cap=0 saved_lr_valid=1 blr_verified=0\n'
T='V398_NAND_RETURN_TRIAL site=0 completed=1\n'
def run(text:str,rc:int=0)->str:
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'log'
        p.write_text(text,encoding='ascii')
        return inspect(p,rc)
class Tests(unittest.TestCase):
    def test_complete_sixteen_real_events_do_not_imply_blr(self):
        s=run(('PRIVATE ADDR 0xDEADBEEF\n'+E+T)*16)
        self.assertIn('entries=16 trials=16',s)
        self.assertIn('witness_verified=1 blr_verified=0',s)
        self.assertIn('sampled_any=0 site_any=0',s)
        self.assertNotIn('PRIVATE ADDR',s)
    def test_valid_pc_witness_is_not_a_blr_witness(self):
        event=E.replace('samples=0','samples=4').replace('site=0','site=1').replace(
            'mapped=0','mapped=1').replace('before_cap=0','before_cap=1')
        trial=T.replace('site=0','site=1')
        out=run((event+trial)*16)
        self.assertIn('sampled_any=1 site_any=1 mapped_any=1 before_cap_any=1',out)
        self.assertIn('blr_verified=0',out)
    def test_bad_or_unpaired_events_rejected(self):
        for broken in ('',E,T,E+E+T,T+E+T,
                       E.replace('saved_lr_valid=1','saved_lr_valid=0')+T,
                       E.replace('site=0','site=1')+T,
                       E.replace('mapped=0','mapped=1')+T,
                       E.replace('before_cap=0','before_cap=1')+T,
                       E+T.replace('site=0','site=1'),
                       E+T.replace('completed=1','completed=0'),
                       E+T+T,(E+T)*17):
            with self.subTest(length=len(broken)):
                self.assertIn('witness_verified=0',run(broken))
if __name__=='__main__':unittest.main()
