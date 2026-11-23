#!/usr/bin/env python3
"""Independent V399 owner original guest return-continuation gate tests."""
from pathlib import Path
import tempfile
import unittest
from audit_v399_native_gate import verify
from test_v398_native_gate import chain as chain398
from test_v398_nand_return_site_audit import T as T398
from test_v399_nand_return_order_audit import E,R,T

T398_POS=T398.replace('site=0','site=1')
def chain(order:str=R,entry:str=E):
    base=chain398(entry,T398_POS)
    return base.replace(entry,entry+order,1).replace(T398_POS,T398_POS+T,1)
def run(data:str,rc:int=0):
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'owner-private.log'
        p.write_text(data,encoding='ascii')
        return verify(p,rc)
class Tests(unittest.TestCase):
    def test_original_complete_chain_and_order_all(self):
        self.assertEqual(run(chain()*16),(True,1,1))
        for rc in (1,124,134):
            self.assertEqual(run(chain()*16,rc),(False,0,0))
        self.assertEqual(run(chain()*15),(False,0,0))
        self.assertEqual(run(chain()*17),(False,0,0))
    def test_no_return_observation_does_not_claim_blr(self):
        no=R.replace('site=1','site=0').replace('mapped=1','mapped=0').replace(
            'bctrl=1','bctrl=0').replace('isfs_after=1','isfs_after=0').replace(
            'ordered=1','ordered=0')
        from test_v398_nand_return_site_audit import E as E398,T as T398_0
        base=chain398(E398,T398_0)
        event=base.replace(E398,E398+no,1).replace(T398_0,T398_0+
             T.replace('ordered=1','ordered=0'),1)
        self.assertEqual(run(event*16),(True,0,0))
    def test_inconsistent_temporal_claims_are_rejected(self):
        for variant in (
            chain().replace('V399_NAND_RETURN_TRIAL ordered=1',
                            'V399_NAND_RETURN_TRIAL ordered=0'),
            chain().replace('V399_NAND_RETURN_ORDER site=1',
                            'V399_NAND_RETURN_ORDER site=0'),
            chain().replace('bctrl=1','bctrl=0').replace('ordered=1','ordered=0'),
            chain().replace('isfs_after=1','isfs_after=0'),
            chain().replace('blr_verified=0','blr_verified=1'),
            chain().replace(T,''),
            chain()+T,
        ):
            with self.subTest(size=len(variant)):
                self.assertEqual(run(chain()*15+variant)[0],False)
if __name__=='__main__':unittest.main()
