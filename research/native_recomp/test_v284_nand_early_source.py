#!/usr/bin/env python3
"""V284 synthetic early NAND r3 source and guarded call sequence regression."""
import unittest
from pathlib import Path
from audit_v284_nand_early_source import CHILD,WRITER,classify,audit

def bl(pc,target):
    d=target-pc
    assert d%4==0 and -(1<<25)<=d<(1<<25)
    return (18<<26)|(d&0x3fffffc)|1
def bc(pc,dest):
    d=dest-pc
    assert d%4==0 and -32768<=d<32768
    return (16<<26)|(12<<21)|(2<<16)|(d&0xfffc)
def cmpwi(r,imm):
    return (11<<26)|(r<<16)|(imm&0xffff)

def fixture():
    w=[0x60000000]*60
    w[20]=bl(CHILD+80,0x8051ac30)
    w[21]=cmpwi(3,0)
    w[22]=bc(CHILD+88,CHILD+188)
    w[43]=bl(CHILD+172,0x8051e150)
    w[44]=cmpwi(3,0)
    w[45]=bc(CHILD+180,CHILD+188)
    w[46]=bl(CHILD+184,WRITER)
    return w

class Tests(unittest.TestCase):
    def test_genuine_call_source_and_both_guards(self):
        out=classify(fixture())
        self.assertIn("compare_offset=84 branch_offset=88 skip_target=188",out)
        self.assertIn("source=call source_offset=80 target=8051ac30",out)

    def test_unknown_or_changed_comparison_fails_closed(self):
        w=fixture()
        w[20]=0x60000000
        self.assertIn("source=unknown",classify(w))
        w=fixture()
        w[21]=cmpwi(4,0)
        with self.assertRaisesRegex(ValueError,"early_comparison"):
            classify(w)
        with self.assertRaisesRegex(ValueError,"digest"):
            audit(b"unverified original ELF")

    def test_ci_privacy(self):
        wf=(Path(__file__).resolve().parents[2]/
            ".github/workflows/wii-v284-nand-early-source.yml").read_text(
                encoding="utf-8")
        self.assertIn("V284_EARLY_AUDIT verified=1",wf)
        self.assertIn("WII_ORIGINAL_ELF_ID",wf)
        self.assertNotIn("upload-artifact",wf)
        self.assertEqual(wf.count("      - name: Remove private owner inputs"),1)

if __name__=="__main__":
    unittest.main()
