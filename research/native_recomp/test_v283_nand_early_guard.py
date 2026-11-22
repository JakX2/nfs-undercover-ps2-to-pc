#!/usr/bin/env python3
"""V283 original-free NAND early/late branch BO/BI regression."""
import unittest
from pathlib import Path
from audit_v283_nand_early_guard import CHILD,WRITER,classify,audit

def bl(pc,target):
    delta=target-pc
    assert delta%4==0 and -(1<<25)<=delta<(1<<25)
    return (18<<26)|(delta&0x3fffffc)|1
def bc(pc,target,bo,bi):
    delta=target-pc
    assert delta%4==0 and -32768<=delta<32768
    return (16<<26)|(bo<<21)|(bi<<16)|(delta&0xfffc)
def cmpwi(reg,val):
    return (11<<26)|(reg<<16)|(val&0xffff)

def synthetic():
    w=[0x60000000]*64
    w[9]=cmpwi(9,3)
    w[10]=bc(CHILD+40,CHILD+220,4,2)
    w[43]=bl(CHILD+172,0x8051e150)
    w[44]=cmpwi(3,0)
    w[45]=bc(CHILD+180,CHILD+188,12,2)
    w[46]=bl(CHILD+184,WRITER)
    return w

class Tests(unittest.TestCase):
    def test_first_guard_and_nearest_guard(self):
        lines=classify(synthetic())
        self.assertEqual(len(lines),2)
        self.assertIn("rank=1 child=8052fa60 branch_offset=40 target_offset=220",lines[0])
        self.assertIn("bo=4 bi=2 cr_field=0 cr_bit=2 cr_expected=0",lines[0])
        self.assertIn("producer=1 cmp_field=0 cmp_ra=9",lines[0])
        self.assertIn("imm_class=3 direct_cr=1",lines[0])
        self.assertIn("rank=2 child=8052fa60 branch_offset=180 target_offset=188",lines[1])
        self.assertIn("bo=12 bi=2 cr_field=0 cr_bit=2 cr_expected=1",lines[1])
        self.assertIn("producer=1 cmp_field=0 cmp_ra=3",lines[1])
        self.assertIn("imm_class=0 direct_cr=1",lines[1])

    def test_wrong_guard_count_fails_closed(self):
        w=synthetic()
        w[10]=0x60000000
        with self.assertRaisesRegex(ValueError,"expected_two_guards"):
            classify(w)
        with self.assertRaisesRegex(ValueError,"digest"):
            audit(b"not an authenticated owner Wii ELF")

    def test_workflow_privacy(self):
        wf=(Path(__file__).resolve().parents[2]/
            ".github/workflows/wii-v283-nand-early-guard.yml").read_text(
                encoding="utf-8")
        self.assertIn("V283_GUARD_AUDIT verified=1",wf)
        self.assertIn("WII_ORIGINAL_ELF_ID",wf)
        self.assertNotIn("upload-artifact",wf)
        self.assertEqual(wf.count("      - name: Remove private owner inputs"),1)

if __name__=="__main__":
    unittest.main()
