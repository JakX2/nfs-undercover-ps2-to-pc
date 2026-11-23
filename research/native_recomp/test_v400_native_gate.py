#!/usr/bin/env python3
"""V400 fail-closed synthetic 16-trial owner-result gate."""
from pathlib import Path
import tempfile
import unittest
from audit_v400_native_gate import verify
from test_v399_native_gate import chain as chain399
from test_v400_nand_parent_resume_audit import E as E400,T as T400
from test_v399_nand_return_order_audit import R as E399,T as T399
def chain(entry=E400,trial=T400):
    previous=chain399()
    return previous.replace(E399,E399+entry,1).replace(T399,T399+trial,1)
def run(data:str,rc:int=0):
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'owner-private.log'
        p.write_text(data,encoding='ascii')
        return verify(p,rc)
class Tests(unittest.TestCase):
    def test_complete_owner_guest_temporal_parent_chain(self):
        self.assertEqual(run(chain()*16),(True,1,1))
        for status in (1,124,134):
            self.assertEqual(run(chain()*16,status),(False,0,0))
        self.assertEqual(run(chain()*15),(False,0,0))
        self.assertEqual(run(chain()*17),(False,0,0))
    def test_uncaptured_parent_does_not_claim_return(self):
        no=E400.replace('site=1','site=0').replace('mapped=1','mapped=0').replace(
            'linked=1','linked=0').replace('selected_first=1','selected_first=0').replace(
            'parent_after=1','parent_after=0').replace('ordered=1','ordered=0')
        nt=T400.replace('ordered=1','ordered=0')
        self.assertEqual(run(chain(no,nt)*16),(True,0,0))
    def test_bad_chain_mismatch_unmapped_and_unpaired(self):
        for bad in (
            chain().replace('V400_NAND_PARENT_TRIAL ordered=1',
                            'V400_NAND_PARENT_TRIAL ordered=0'),
            chain().replace('V400_NAND_PARENT_RESUME site=1',
                            'V400_NAND_PARENT_RESUME site=0'),
            chain().replace('selected_first=1','selected_first=0'),
            chain().replace('parent_after=1','parent_after=0'),
            chain().replace('blr_verified=0','blr_verified=1'),
            chain().replace(T400,''),
            chain()+T400,
        ):
            with self.subTest(size=len(bad)):
                self.assertEqual(run(chain()*15+bad)[0],False)
if __name__=="__main__":unittest.main()
