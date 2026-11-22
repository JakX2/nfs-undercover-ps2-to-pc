#!/usr/bin/env python3
"""V272 original-free PPC immediate byte-store source and ownership tests."""
import unittest
from pathlib import Path
from audit_v272_sc_writer_values import classify_sites,audit,HELPER

def li(rt,val):
    return 14<<26|rt<<21|(val&0xffff)

class Tests(unittest.TestCase):
    def test_source_immediate_class_and_groups(self):
        funcs={HELPER:256,0x80530ba0:256,0x80530dbc:256}
        sample=[
            (HELPER+44,0,li(0,1)),
            (HELPER+240,29,li(29,0)),
            (0x80530ba0+8,3,li(3,3)),
            (0x80530ba0+16,4,0x60000000),
            (0x80530dbc+12,5,li(5,2)),
        ]
        result,lines=classify_sites(sample,funcs)
        self.assertEqual(result["stores"],5)
        self.assertEqual(result["const3"],1)
        self.assertEqual(result["helper_one"],1)
        self.assertEqual(result["helper_zero"],1)
        self.assertEqual(result["unknown"],1)
        self.assertIn("c3=1",lines[2])
        self.assertNotIn("0x60000000","\n".join(lines))
        self.assertEqual(len(lines),4)

    def test_fail_closed_hash(self):
        with self.assertRaisesRegex(ValueError,"digest"):
            audit(b"not original Wii ELF")

    def test_public_cannot_upload_proprietary_data(self):
        wf=(Path(__file__).resolve().parents[2]/
            ".github/workflows/wii-v272-sc-writer-values.yml").read_text(encoding="utf-8")
        self.assertIn("V272_WRITER_AUDIT verified=1",wf)
        self.assertIn("WII_ORIGINAL_ELF_ID",wf)
        self.assertNotIn("upload-artifact",wf)
        self.assertEqual(wf.count("      - name: Remove private owner inputs"),1)

if __name__=="__main__":
    unittest.main()
