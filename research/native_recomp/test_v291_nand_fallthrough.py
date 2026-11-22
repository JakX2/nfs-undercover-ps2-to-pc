#!/usr/bin/env python3
"""V291 original-free NAND first zero-check fallthrough tests."""
import unittest
from pathlib import Path
from audit_v291_nand_fallthrough import CHILD,scan,audit,cr0_effect

def branch(pc,dst,op=18,link=False):
    d=dst-pc
    assert d%4==0
    if op==18:return (18<<26)|(d&0x03fffffc)|int(link)
    return (16<<26)|(4<<21)|(2<<16)|(d&0xfffc)

def sample():
    words=[0x60000000]*60
    words[0]=(37<<26)|(1<<21)|(1<<16)|0xffd0
    words[1]=0x7c0802a6
    words[2]=(11<<26)|(3<<16)
    words[6]=branch(CHILD+24,CHILD+92,16)
    return words

class Tests(unittest.TestCase):
    def test_original_zero_check_without_interrupting_branches(self):
        out=scan(sample())
        self.assertIn("cr0=preserved between_keep=3 between_write=0",out[0])
        self.assertIn("events=0 conditional=0 direct_call=0 direct_jump=0",out[0])

    def test_unconditional_jump_bypasses_service(self):
        words=sample()
        words[9]=branch(CHILD+36,CHILD+100)
        out=scan(words)
        self.assertIn("events=1 conditional=0 direct_call=0 direct_jump=1",out[0])
        self.assertIn("offset=36 kind=direct_jump target_offset=100",out[1])

    def test_cr0_clobber_fails_closed_instead_of_ignoring(self):
        words=sample()
        words[4]=(28<<26)|(4<<21)|(5<<16)|0xff
        out=scan(words)
        self.assertIn("cr0=clobbered between_keep=2 between_write=1",out[0])
        words=sample()
        words[4]=0x00000000
        out=scan(words)
        self.assertIn("cr0=inconclusive between_keep=2 between_write=0 between_unknown=1",out[0])
        words=sample()
        words[0]=(14<<26)|(3<<21)|(3<<16)
        with self.assertRaisesRegex(ValueError,"entry_r3_not_preserved"):scan(words)
        with self.assertRaisesRegex(ValueError,"original_sha"):audit(b"invalid owner ELF")

    def test_ci_private(self):
        wf=(Path(__file__).resolve().parents[2]/
            ".github/workflows/wii-v291-nand-fallthrough.yml").read_text()
        self.assertIn("V291_NAND_FLOW_AUDIT verified=1",wf)
        self.assertIn("WII_ORIGINAL_ELF_ID",wf)
        self.assertNotIn("upload-artifact",wf)
        self.assertEqual(wf.count("      - name: Remove private owner inputs"),1)

if __name__=="__main__":
    unittest.main()
