#!/usr/bin/env python3
"""V280 original-free PowerPC r3 guard-producer tests."""
import unittest
from pathlib import Path
from audit_v280_nand_r3_producer import CHILD,WRITER,trace_source,classify,audit

def bl(pc,target):
    d=target-pc
    assert d%4==0 and -(1<<25)<=d<(1<<25)
    return (18<<26)|(d&0x3fffffc)|1

def bc(pc,dest,bo=12,bi=2):
    d=dest-pc
    assert d%4==0 and -32768<=d<32768
    return (16<<26)|(bo<<21)|(bi<<16)|(d&0xfffc)

def fixture():
    words=[0x60000000]*52
    words[34]=bl(CHILD+34*4,0x8052f790)
    words[44]=(11<<26)|(3<<16) # cmpwi r3,0
    words[45]=bc(CHILD+45*4,CHILD+47*4)
    words[46]=bl(CHILD+46*4,WRITER)
    return words

class Tests(unittest.TestCase):
    def test_direct_call_result_used_by_guard(self):
        words=fixture()
        src=trace_source(words,44,3)
        self.assertEqual(src["kind"],"call")
        self.assertEqual(src["offset"],136)
        self.assertEqual(src["target"],0x8052f790)
        report=classify(words)
        self.assertIn("cmp_offset=176 guarded_call=184",report)
        self.assertIn("source=call source_offset=136 source_target=8052f790",report)

    def test_memory_source_or_interrupting_branch(self):
        words=fixture()
        words[43]=(32<<26)|(3<<21)|(29<<16)|8
        value=trace_source(words,44)
        self.assertEqual((value["kind"],value["width"],value["base"],value["disp"]),
                         ("load",4,29,8))
        words[43]=bc(CHILD+43*4,CHILD+45*4)
        self.assertEqual(trace_source(words,44)["kind"],"barrier")
        words[43]=0x60000000
        with self.assertRaisesRegex(ValueError,"geometry"):
            trace_source(words,999)
        with self.assertRaisesRegex(ValueError,"digest"):
            audit(b"no original Wii executable")

    def test_private_ci(self):
        wf=(Path(__file__).resolve().parents[2]/
            ".github/workflows/wii-v280-nand-r3-producer.yml").read_text(
                encoding="utf-8")
        self.assertIn("V280_R3_AUDIT verified=1",wf)
        self.assertIn("WII_ORIGINAL_ELF_ID",wf)
        self.assertNotIn("upload-artifact",wf)
        self.assertEqual(wf.count("      - name: Remove private owner inputs"),1)

if __name__=="__main__":
    unittest.main()
