#!/usr/bin/env python3
"""V277 synthetic direct BL callgraph and owner boundaries regression."""
import unittest
from pathlib import Path
from audit_v277_sc_writer_callers import find_calls,classify,audit,TARGETS

def bl(pc,target,lk=True):
    d=target-pc
    assert d%4==0 and -(1<<25)<=d<(1<<25)
    return (18<<26)|(d&0x03fffffc)|int(lk)

class Tests(unittest.TestCase):
    def test_correct_target_and_linkbit(self):
        base=0x8051f000
        words=[bl(base,TARGETS[0]),
               bl(base+4,TARGETS[1],False),
               bl(base+8,TARGETS[2]),
               bl(base+12,TARGETS[2]+4),
               0x4e800420]
        result=find_calls(words,base)
        self.assertEqual(result,[(base,TARGETS[0]),(base+8,TARGETS[2])])
        fake={base:0x100}
        rows=classify(result,fake)
        self.assertIn("direct_calls=2 caller_pairs=2",rows[0])
        self.assertIn(f"target={TARGETS[0]:08x} calls=1 callers=1",rows[1])
        self.assertEqual(sum("V277_SC_TARGET" in x for x in rows),6)
        self.assertNotIn("0x4e800420","\n".join(rows))

    def test_digest_and_geometry_fail_closed(self):
        with self.assertRaisesRegex(ValueError,"geometry"):
            find_calls([0],1)
        with self.assertRaisesRegex(ValueError,"digest"):
            audit(b"not original Wii ELF")

    def test_private_job_keeps_code_private(self):
        wf=(Path(__file__).resolve().parents[2]/
            ".github/workflows/wii-v277-sc-writer-callers.yml").read_text(encoding="utf-8")
        self.assertIn("V277_SC_CALL_AUDIT verified=1",wf)
        self.assertIn("WII_ORIGINAL_ELF_ID",wf)
        self.assertNotIn("upload-artifact",wf)
        self.assertEqual(wf.count("      - name: Remove private owner inputs"),1)

if __name__=="__main__":
    unittest.main()
