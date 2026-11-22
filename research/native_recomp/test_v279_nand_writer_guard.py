#!/usr/bin/env python3
"""V279 synthetic Wii NAND-child BL and conditional skip-guard regressions."""
import unittest
from pathlib import Path
from audit_v279_nand_writer_guard import CHILD,WRITER,classify,audit,sanitized

def bl(pc,target,link=True):
    d=target-pc
    assert d%4==0 and -(1<<25)<=d<(1<<25)
    return (18<<26)|(d&0x03fffffc)|int(link)
def bc(pc,target,bo=4,bi=2):
    d=target-pc
    assert d%4==0 and -32768<=d<32768
    return (16<<26)|(bo<<21)|(bi<<16)|(d&0xfffc)

class Tests(unittest.TestCase):
    def test_signed_edge_and_comparison(self):
        w=[0x60000000]*48
        w[3]=(10<<26)|(5<<16)|3
        w[4]=bc(CHILD+16,CHILD+36)
        w[6]=bl(CHILD+24,WRITER)
        value=classify(w,CHILD)
        self.assertEqual(value["call_offset"],24)
        self.assertEqual(value["skip_cond"],1)
        self.assertEqual(value["nearest_skip_offset"],16)
        self.assertEqual(value["nearest_target_offset"],36)
        self.assertEqual(value["bo"],4)
        self.assertEqual(value["bi"],2)
        self.assertEqual(value["producer_kind"],2)
        self.assertEqual(value["producer_ra"],5)
        self.assertEqual(value["producer_imm_class"],3)
        self.assertIn("direct=1",sanitized(value))

    def test_unknown_or_ambiguous_fail_closed(self):
        w=[0x60000000]*48
        w[6]=bl(CHILD+24,WRITER)
        self.assertEqual(classify(w,CHILD)["skip_cond"],0)
        w[7]=bl(CHILD+28,WRITER)
        with self.assertRaisesRegex(ValueError,"callsite_count"):
            classify(w,CHILD)
        with self.assertRaisesRegex(ValueError,"digest"):
            audit(b"not original ELF")

    def test_private_ci_guards(self):
        wf=(Path(__file__).resolve().parents[2]/
            ".github/workflows/wii-v279-nand-writer-guard.yml").read_text(
                encoding="utf-8")
        self.assertIn("V279_NAND_CALL_AUDIT verified=1",wf)
        self.assertIn("WII_ORIGINAL_ELF_ID",wf)
        self.assertNotIn("upload-artifact",wf)
        self.assertEqual(wf.count("      - name: Remove private owner inputs"),1)

if __name__=="__main__":
    unittest.main()
