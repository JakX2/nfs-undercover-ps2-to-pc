#!/usr/bin/env python3
"""Independent V398 owner-result gate with synthetic guest marker chains."""
from pathlib import Path
import tempfile
import unittest
from audit_v398_native_gate import verify
from test_v397_native_gate import EVENT as V397_EVENT,T397
from test_v398_nand_return_site_audit import E,T

def chain(entry:str=E,trial:str=T)->str:
    return V397_EVENT.replace(T397,entry+T397+trial)

def run(text:str,rc:int=0)->bool:
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/"private-owner-native.log"
        p.write_text(text,encoding="ascii")
        return verify(p,rc)

class Tests(unittest.TestCase):
    def test_full_16_trial_guest_chain_verified_without_return_claim(self):
        self.assertTrue(run(chain()*16))
        for rc in (1,124,134):
            self.assertFalse(run(chain()*16,rc))
        self.assertFalse(run(chain()*15))
        self.assertFalse(run(chain()*17))
    def test_return_site_witness_does_not_claim_blr(self):
        entry=E.replace("samples=0","samples=2").replace("site=0","site=1").replace(
            "mapped=0","mapped=1").replace("before_cap=0","before_cap=1")
        trial=T.replace("site=0","site=1")
        self.assertTrue(run(chain(entry,trial)*16))
    def test_corrupt_completeness_and_state_fail_closed(self):
        for variant in (
            chain().replace("saved_lr_valid=1","saved_lr_valid=0"),
            chain().replace("blr_verified=0","blr_verified=1"),
            chain().replace("samples=0","samples=65"),
            chain().replace("site=0","site=1"),
            chain().replace("mapped=0","mapped=1"),
            chain().replace("before_cap=0","before_cap=1"),
            chain().replace("V397_NAND_ORIGINS_TRIAL completed=1",
                            "V397_NAND_ORIGINS_TRIAL completed=0"),
            chain().replace("V398_NAND_RETURN_TRIAL site=0 completed=1",
                            "V398_NAND_RETURN_TRIAL site=0 completed=0"),
            chain().replace(T,""),
            chain()+T,
        ):
            with self.subTest(len=len(variant)):
                self.assertFalse(run(chain()*15+variant))
    def test_output_is_private_by_construction(self):
        self.assertTrue(run(("SECRET 0x7fc12345\n"+chain())*16))

if __name__=="__main__":
    unittest.main()
