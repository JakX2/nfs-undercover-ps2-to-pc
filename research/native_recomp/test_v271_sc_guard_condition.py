#!/usr/bin/env python3
"""V271 synthetic PPC BO/BI skip-store edge and CR producer tests."""
import unittest
from pathlib import Path
from audit_v271_sc_guard_condition import classify,audit,HELPER

def op(opcode,rt,ra,imm):
    return opcode<<26|rt<<21|ra<<16|(imm&0xffff)

def cmpwi(ra,imm):
    return 11<<26|ra<<16|(imm&0xffff)

def bc(pc,target):
    delta=target-pc
    assert delta%4==0 and -32768<=delta<32768
    return 16<<26|12<<21|2<<16|(delta&0xfffc)

def fixture():
    w=[0x60000000]*71
    w[6]=op(34,4,13,-3176)
    w[7]=cmpwi(4,1)
    w[8]=bc(HELPER+32,HELPER+48)
    w[9]=op(14,6,0,1)
    w[10]=op(38,6,13,-3176)
    w[16]=cmpwi(3,0)
    w[17]=bc(HELPER+68,HELPER+88)
    w[19]=op(14,7,0,0)
    w[20]=op(38,7,13,-3176)
    return w

class Tests(unittest.TestCase):
    def test_guards_and_comparators(self):
        rows=classify(fixture())
        self.assertEqual(len(rows),2)
        self.assertIn("rank=1 store_offset=40 branch_offset=32 target_offset=48",rows[0])
        self.assertIn("bo=12 bi=2 cr_field=0 cr_bit=2",rows[0])
        self.assertIn("direct_cmp=1 cmp_kind=1 cmp_ra=4 cmp_imm_class=1 read_rt=4 status_cmp=1",rows[0])
        self.assertIn("rank=2 store_offset=80 branch_offset=68 target_offset=88",rows[1])
        self.assertIn("direct_cmp=1 cmp_kind=1 cmp_ra=3 cmp_imm_class=0 read_rt=4 status_cmp=0",rows[1])
        self.assertNotIn("0x60000000","\n".join(rows))

    def test_fail_closed(self):
        with self.assertRaisesRegex(ValueError,"status_sites"):
            classify([0x60000000]*71)
        with self.assertRaisesRegex(ValueError,"digest"):
            audit(b"not the SHA-pinned original ELF")
        w=fixture()
        w[14]=bc(HELPER+56,HELPER+88)
        with self.assertRaisesRegex(ValueError,"guard_count"):
            classify(w)

    def test_owner_ci_guards(self):
        wf=(Path(__file__).resolve().parents[2]/
            ".github/workflows/wii-v271-sc-guard-condition.yml").read_text(encoding="utf-8")
        self.assertIn("V271_GUARD_AUDIT verified=1",wf)
        self.assertIn("WII_ORIGINAL_ELF_ID",wf)
        self.assertNotIn("upload-artifact",wf)
        self.assertEqual(wf.count("      - name: Remove private owner inputs"),1)

if __name__=="__main__":
    unittest.main()
