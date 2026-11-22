#!/usr/bin/env python3
"""V288 PowerPC CR0-producing instructions and NAND early guard."""
import unittest
from pathlib import Path
from audit_v288_nand_early_cr import CHILD,producer,classify,audit

def bc(pc,dest):
    d=dest-pc
    assert d%4==0 and -32768<=d<32768
    return (16<<26)|(4<<21)|(2<<16)|(d&0xfffc)
def cmpw(ra,rb):
    return (31<<26)|(ra<<16)|(rb<<11)
def cmplwi(ra,imm):
    return (10<<26)|(ra<<16)|(imm&0xffff)

class Tests(unittest.TestCase):
    def fixture(self):
        w=[0x60000000]*48
        w[5]=cmpw(3,4)
        w[6]=bc(CHILD+24,CHILD+92)
        return w

    def test_register_compare_cr0(self):
        value=classify(self.fixture())
        self.assertIn("producer=cmpreg producer_offset=20 cr_field=0 ra=3 rb=4",value)
        self.assertIn("cr_expected=0",value)
        w=self.fixture()
        w[5]=0x60000000
        self.assertIn("producer=entry producer_offset=-1",classify(w))
        w[4]=cmplwi(3,3)
        self.assertIn("producer=cmplimm producer_offset=16",classify(w))

    def test_unsupported_or_changed_branch_fails_closed(self):
        w=self.fixture()
        w[6]=0x60000000
        with self.assertRaisesRegex(ValueError,"early_branch"):
            classify(w)
        with self.assertRaisesRegex(ValueError,"digest"):
            audit(b"invalid original ELF")
        self.assertEqual(producer(0x60000000)[0],"none")

    def test_private_ci(self):
        wf=(Path(__file__).resolve().parents[2]/
            ".github/workflows/wii-v288-nand-early-cr.yml").read_text(encoding="utf-8")
        self.assertIn("V288_EARLY_CR_AUDIT verified=1",wf)
        self.assertIn("WII_ORIGINAL_ELF_ID",wf)
        self.assertNotIn("upload-artifact",wf)
        self.assertEqual(wf.count("      - name: Remove private owner inputs"),1)

if __name__=="__main__":
    unittest.main()
