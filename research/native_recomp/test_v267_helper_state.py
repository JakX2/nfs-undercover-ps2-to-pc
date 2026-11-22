#!/usr/bin/env python3
"""V267 synthetic helper r3 and Wii SDA load semantic regressions."""
import unittest
from pathlib import Path
from audit_v267_helper_state import (
    HELPER, DISABLE, RESTORE, GETTIME, classify, audit, sanitized,
)


def bl(pc:int,target:int)->int:
    d=target-pc
    assert -(1<<25)<=d<(1<<25) and d%4==0
    return (18<<26)|(d&0x3fffffc)|1


def l(op:int,rd:int,ra:int,offset:int)->int:
    return (op<<26)|(rd<<21)|(ra<<16)|(offset&0xffff)


class Tests(unittest.TestCase):
    def test_synthetic_sda_and_return_structure(self):
        w=[0x60000000]*72
        w[2]=l(34,4,13,-3176)
        w[3]=l(32,3,13,-3176)
        w[4]=l(32,4,13,-3000)
        w[5]=l(32,3,8,24)
        w[6]=l(14,3,0,1)
        w[7]=l(14,3,0,0)
        w[8]=l(14,3,0,7)
        w[9]=0x4e800020
        w[10]=bl(HELPER+40,DISABLE)
        w[11]=bl(HELPER+44,RESTORE)
        w[12]=bl(HELPER+48,GETTIME)
        w[13]=l(10,0,3,1)
        out=classify(HELPER,w)
        expected={"size_ins":72,"sc_byte":1,"sc_direct":2,
                  "sda_loads":3,"sda_other":1,"lr_branch":1,
                  "blr_unconditional":1,"r3_li_one":1,"r3_li_zero":1,
                  "r3_li_other":1,"r3_load":2,"cmp_r3_one":1,
                  "disable":1,"restore":1,"gettime":1,"mftb":0}
        for key,value in expected.items():
            self.assertEqual(out[key],value,key)
        self.assertIn("V267_HELPER_STATE size_ins=72",sanitized(out))
        self.assertNotIn("0x60000000",sanitized(out))

    def test_fail_closed(self):
        with self.assertRaisesRegex(ValueError,"geometry"):
            classify(HELPER+4,[0x60000000]*72)
        with self.assertRaisesRegex(ValueError,"geometry"):
            classify(HELPER,[])
        with self.assertRaisesRegex(ValueError,"digest"):
            audit(b"not the original Wii ELF")

    def test_owner_only_ci_and_privacy(self):
        wf=(Path(__file__).resolve().parents[2]/
            ".github/workflows/wii-v267-helper-state.yml").read_text(encoding="utf-8")
        self.assertIn("V267_HELPER_AUDIT verified=1",wf)
        self.assertIn("WII_ORIGINAL_ELF_ID",wf)
        self.assertNotIn("upload-artifact",wf)
        self.assertEqual(wf.count("      - name: Remove private owner inputs"),1)


if __name__=="__main__":
    unittest.main()
