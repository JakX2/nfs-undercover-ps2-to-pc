#!/usr/bin/env python3
"""V287 original-free PPC NAND child pre-guard branch/call tests."""
import unittest
from pathlib import Path
from audit_v287_nand_prefix import CHILD,classify,audit,BOUND

def bl(pc,target):
    d=target-pc
    assert d%4==0 and -(1<<25)<=d<(1<<25)
    return 18<<26|(d&0x3fffffc)|1
def bc(pc,target,bo=4,bi=2):
    d=target-pc
    assert d%4==0 and -32768<=d<32768
    return 16<<26|bo<<21|bi<<16|(d&0xfffc)
def cmpwi(ra,imm):
    return 11<<26|(ra<<16)|(imm&0xffff)

class Tests(unittest.TestCase):
    def test_two_calls_and_forward_skip_classified(self):
        w=[0x60000000]*48
        w[1]=bl(CHILD+4,0x8051a200)
        w[8]=bl(CHILD+32,0x8051a400)
        w[10]=cmpwi(5,0)
        w[11]=bc(CHILD+44,CHILD+120)
        report=classify(w)
        self.assertIn("bytes=80 calls=2 conditional=1 forward_beyond_early=1",report[0])
        self.assertIn("rank=1 offset=4 target=8051a200",report[1])
        self.assertIn("rank=2 offset=32 target=8051a400",report[2])
        self.assertIn("rank=1 offset=44 dest_offset=120 bo=4 bi=2",report[3])
        self.assertIn("prev_cmp_kind=1 cmp_field=0 cmp_ra=5 imm_class=0",report[3])

    def test_bounds_and_digest(self):
        with self.assertRaisesRegex(ValueError,"geometry"):
            classify([0]*2)
        with self.assertRaisesRegex(ValueError,"digest"):
            audit(b"not the original ELF")

    def test_ci_stages_original_privately(self):
        wf=(Path(__file__).resolve().parents[2]/
            ".github/workflows/wii-v287-nand-prefix.yml").read_text(
                encoding="utf-8")
        self.assertIn("V287_PREFIX_AUDIT verified=1",wf)
        self.assertIn("WII_ORIGINAL_ELF_ID",wf)
        self.assertNotIn("upload-artifact",wf)
        self.assertEqual(wf.count("      - name: Remove private owner inputs"),1)

if __name__=="__main__":
    unittest.main()
