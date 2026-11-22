#!/usr/bin/env python3
"""V286 synthetic PowerPC guarded return-producing function structure."""
import unittest
from pathlib import Path
from audit_v286_nand_early_source_shape import FUNC,analyze_words,audit

def bl(pc,target):
    d=target-pc
    assert d%4==0 and -(1<<25)<=d<(1<<25)
    return 18<<26|(d&0x3fffffc)|1
def li(rd,value):
    return 14<<26|rd<<21|(value&0xffff)
def lbz(rt,ra,off):
    return 34<<26|rt<<21|ra<<16|(off&0xffff)

class Tests(unittest.TestCase):
    def test_direct_calls_and_return_categories(self):
        w=[0x60000000]*14
        w[1]=bl(FUNC+4,0x8051e180)
        w[2]=bl(FUNC+8,0x8051e180)
        w[3]=(16<<26)|(12<<21)|(2<<16)|8
        w[4]=lbz(4,13,-3176)
        w[7]=li(3,0)
        w[8]=0x4e800020
        report=analyze_words(w)
        self.assertIn("instructions=14 direct_calls=2 target_count=1",report[0])
        self.assertIn("cond_branches=1 bclr=1 literal_return0=1",report[0])
        self.assertIn("sc_read=1 sc_write=0",report[0])
        self.assertIn("target=8051e180 count=2",report[1])

    def test_owner_only_and_invalid_bounds(self):
        with self.assertRaisesRegex(ValueError,"geometry"):
            analyze_words([0]*14,FUNC+4)
        with self.assertRaisesRegex(ValueError,"digest"):
            audit(b"not Wii ELF")
        wf=(Path(__file__).resolve().parents[2]/
            ".github/workflows/wii-v286-nand-early-source-shape.yml").read_text(
                encoding="utf-8")
        self.assertIn("V286_SOURCE_AUDIT verified=1",wf)
        self.assertIn("WII_ORIGINAL_ELF_ID",wf)
        self.assertNotIn("upload-artifact",wf)
        self.assertEqual(wf.count("      - name: Remove private owner inputs"),1)

if __name__=="__main__":
    unittest.main()
