#!/usr/bin/env python3
"""V270 original-free SC byte-store guards and source-kind tests."""
import unittest
from pathlib import Path
from audit_v270_sc_writer_guards import HELPER,classify,audit,source_kind

def op(opcode,rt,ra,imm):
    return opcode<<26 | rt<<21 | ra<<16 | (imm&0xffff)

def bc(pc,target):
    d=target-pc
    assert d%4==0 and -32768<=d<32768
    return 16<<26 | 12<<21 | 2<<16 | (d&0xfffc)

def fixture():
    w=[0x60000000]*71
    w[3]=op(34,5,13,-3176)
    w[8]=bc(HELPER+32,HELPER+48)
    w[9]=op(14,6,0,1)
    w[10]=op(38,6,13,-3176)
    w[17]=bc(HELPER+68,HELPER+88)
    w[19]=op(14,7,0,0)
    w[20]=op(38,7,13,-3176)
    return w

class Tests(unittest.TestCase):
    def test_two_original_free_guarded_stores(self):
        lines=classify(fixture(),HELPER)
        self.assertEqual(len(lines),3)
        self.assertIn("read_offset=12 store1_offset=40 store2_offset=80",lines[0])
        self.assertIn("rank=1 offset=40 rs=6 prev_kind=1 prev_const=1 skip_cond=1",lines[1])
        self.assertIn("rank=2 offset=80 rs=7 prev_kind=1 prev_const=0 skip_cond=1",lines[2])
        self.assertEqual(source_kind(op(14,8,0,1),8),(1,1))
        self.assertEqual(source_kind(op(34,8,13,12),8),(2,-1))

    def test_negative_fail_closed(self):
        with self.assertRaisesRegex(ValueError,"geometry"):
            classify(fixture(),HELPER+4)
        with self.assertRaisesRegex(ValueError,"status_sites"):
            classify([0x60000000]*71,HELPER)
        with self.assertRaisesRegex(ValueError,"digest"):
            audit(b"not the owner Wii ELF")

    def test_ci_original_is_private(self):
        wf=(Path(__file__).resolve().parents[2]/
            ".github/workflows/wii-v270-sc-guards.yml").read_text(encoding="utf-8")
        self.assertIn("V270_GUARD_AUDIT verified=1",wf)
        self.assertIn("WII_ORIGINAL_ELF_ID",wf)
        self.assertNotIn("upload-artifact",wf)
        self.assertEqual(wf.count("      - name: Remove private owner inputs"),1)

if __name__=="__main__":
    unittest.main()
