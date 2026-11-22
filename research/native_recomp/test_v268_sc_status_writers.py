#!/usr/bin/env python3
"""V268 original-free exact r13-3176 read/write and symbol ownership tests."""
import unittest
from pathlib import Path
from audit_v268_sc_status_writers import access,scan,owners,audit,sanitized

def wi(op,reg,base,disp):
    return (op<<26)|(reg<<21)|(base<<16)|(disp&0xffff)


class Tests(unittest.TestCase):
    def test_byte_vs_wide_and_exact_status_offset(self):
        self.assertEqual(access(wi(34,4,13,-3176)),"byte_read")
        self.assertEqual(access(wi(38,5,13,-3176)),"byte_write")
        self.assertEqual(access(wi(32,6,13,-3176)),"wide_read")
        self.assertEqual(access(wi(36,7,13,-3176)),"wide_write")
        self.assertEqual(access(wi(34,4,13,-3172)),"other")
        self.assertEqual(access(wi(38,5,12,-3176)),"other")
        w=[0x60000000,wi(34,3,13,-3176),wi(38,3,13,-3176)]
        self.assertEqual(scan(w,0x8052f830),
                         [(0x8052f834,"byte_read"),(0x8052f838,"byte_write")])
        with self.assertRaisesRegex(ValueError,"geometry"):
            scan(w,0x8052f831)

    def test_owner_mapping_and_censored_rows(self):
        entries=[(0x8052f834,"byte_read"),(0x8052f83c,"byte_write"),
                 (0x8052f900,"byte_write"),(0x8052e100,"wide_write")]
        f={0x8052f830:32,0x8052f8f0:32}
        own=owners(entries,f)
        self.assertEqual(own,[(0x8052f830,"byte_read"),(0x8052f830,"byte_write"),
                              (0x8052f8f0,"byte_write"),(0,"wide_write")])
        summary={"sections":1,"read":1,"write":3,"byte_read":1,
                 "byte_write":2,"helper_read":1,"helper_write":1,
                 "writer_owners":3,"unmapped":1}
        rows=sanitized(summary,own)
        self.assertEqual(len(rows),4)
        self.assertTrue(rows[1].startswith("V268_SC_WRITER rank=1"))
        self.assertNotIn("0x60000000","\n".join(rows))

    def test_sha_gate_and_owner_only_ci(self):
        with self.assertRaisesRegex(ValueError,"digest"):
            audit(b"not the owner Wii ELF")
        wf=(Path(__file__).resolve().parents[2]/
            ".github/workflows/wii-v268-sc-writers.yml").read_text(encoding="utf-8")
        self.assertIn("V268_SC_AUDIT verified=1",wf)
        self.assertIn("WII_ORIGINAL_ELF_ID",wf)
        self.assertNotIn("upload-artifact",wf)
        self.assertEqual(wf.count("      - name: Remove private owner inputs"),1)


if __name__=="__main__":
    unittest.main()
