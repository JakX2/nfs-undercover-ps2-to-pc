#!/usr/bin/env python3
"""V275 exact PPC +0x188 access and source-to-status link regressions."""
import unittest
from pathlib import Path
from audit_v275_sc_field_xref import field_access,input_edges,audit

OWNER=0x80530ba0
def lwz(rt,ra,offset):
    return 32<<26|rt<<21|ra<<16|(offset&0xffff)
def stw(rt,ra,offset):
    return 36<<26|rt<<21|ra<<16|(offset&0xffff)
def stb(rt,ra,offset):
    return 38<<26|rt<<21|ra<<16|(offset&0xffff)

class Tests(unittest.TestCase):
    def test_input_links_and_other_struct_guards(self):
        words=[0x60000000,lwz(5,31,392),stb(5,13,-3176),
               lwz(4,3,392),stb(4,13,-3176)]
        self.assertEqual(input_edges(OWNER,words),[(8,4,31,5),(16,12,3,4)])
        self.assertEqual(field_access(lwz(5,31,392)),"load")
        self.assertEqual(field_access(stw(5,31,392)),"write_word")
        self.assertEqual(field_access(stb(5,31,392)),"write_byte")
        self.assertEqual(field_access(lwz(5,31,396)),"other")
        self.assertEqual(field_access(lwz(5,0,392)),"other")
        wrong=[lwz(5,31,392),stb(6,13,-3176)]
        self.assertEqual(input_edges(OWNER,wrong),[])

    def test_fail_closed(self):
        with self.assertRaisesRegex(ValueError,"geometry"):
            input_edges(0x8052f830,[0]*2)
        with self.assertRaisesRegex(ValueError,"digest"):
            audit(b"not the original owner Wii ELF")

    def test_ci_privacy_and_source(self):
        wf=(Path(__file__).resolve().parents[2]/
            ".github/workflows/wii-v275-sc-field-xref.yml").read_text(encoding="utf-8")
        self.assertIn("V275_FIELD_AUDIT verified=1",wf)
        self.assertIn("WII_ORIGINAL_ELF_ID",wf)
        self.assertNotIn("upload-artifact",wf)
        self.assertEqual(wf.count("      - name: Remove private owner inputs"),1)

if __name__=="__main__":
    unittest.main()
