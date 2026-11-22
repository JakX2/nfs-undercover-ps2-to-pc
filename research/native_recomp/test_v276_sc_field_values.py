#!/usr/bin/env python3
"""V276 PowerPC source-byte and base-register field-store probes."""
import unittest
from pathlib import Path
from audit_v276_sc_field_values import examine,audit
from audit_v275_sc_field_xref import FIELD

OWNER=0x80530ba0
def op(code,rt,base,disp):
    return code<<26|rt<<21|base<<16|(disp&0xffff)
def li(r,v):return op(14,r,0,v)
def store_field(rs,ra):return op(36,rs,ra,FIELD)
def load_field(rt,ra):return op(32,rt,ra,FIELD)
def store_sc(rs):return op(38,rs,13,-3176)

class Tests(unittest.TestCase):
    def test_same_register_source_and_local_constant(self):
        words=[li(5,3),store_field(5,29),load_field(0,29),
               store_sc(0),li(5,2),store_field(5,29),
               load_field(0,29),store_sc(0)]+[0x60000000]*8
        out=examine(OWNER,words)
        self.assertIn("base_reg=29 loads=2 writes=2",out[0])
        self.assertIn("same_base=1 source_reg=5 source=byte3",out[1])
        self.assertIn("same_base=1 source_reg=5 source=byte2",out[2])

    def test_different_base_never_claim_alias(self):
        words=[li(5,3),store_field(5,31),load_field(0,29),
               store_sc(0),load_field(0,29),store_sc(0)]+[0x60000000]*8
        out=examine(OWNER,words)
        self.assertIn("same_base=0 source_reg=5 source=byte3",out[1])
        with self.assertRaisesRegex(ValueError,"geometry"):
            examine(0x8052f830,words)
        with self.assertRaisesRegex(ValueError,"digest"):
            audit(b"not authenticated Wii ELF")

    def test_private_original_workflow(self):
        wf=(Path(__file__).resolve().parents[2]/
            ".github/workflows/wii-v276-sc-field-values.yml").read_text(encoding="utf-8")
        self.assertIn("V276_FIELD_VALUES verified=1",wf)
        self.assertIn("WII_ORIGINAL_ELF_ID",wf)
        self.assertNotIn("upload-artifact",wf)
        self.assertEqual(wf.count("      - name: Remove private owner inputs"),1)

if __name__=="__main__":
    unittest.main()
