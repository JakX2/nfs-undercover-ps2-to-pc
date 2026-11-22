#!/usr/bin/env python3
"""V290 original-free PPC register-liveness and branch tests."""
import unittest
from pathlib import Path
from audit_v290_nand_input_liveness import CHILD,classify,audit,effect

def fixture():
    words=[0x60000000]*48
    words[0]=(37<<26)|(1<<21)|(1<<16)|0xffd0 # stwu r1,-48(r1)
    words[1]=0x7c0802a6                     # mflr r0
    words[2]=(11<<26)|(3<<16)                # cmpwi r3,0
    d=(CHILD+92)-(CHILD+24)
    words[6]=(16<<26)|(4<<21)|(2<<16)|(d&0xfffc) # bne +92
    return words

class Tests(unittest.TestCase):
    def test_preserved_and_nonzero_skip(self):
        result=classify(fixture())
        self.assertIn("nonzero_skips=1 zero_fallthrough=1 preserved=1",result)
        self.assertIn("i0=storeupdate e0=keep i1=special e1=keep",result)
    def test_clobber_and_unknown_fail_closed(self):
        w=fixture()
        w[0]=(14<<26)|(3<<21)|(3<<16)
        self.assertIn("preserved=0 write=1",classify(w))
        w=fixture()
        w[1]=(31<<26)|(3<<16)|(999<<1)
        self.assertIn("preserved=0 write=0 unknown=1",classify(w))
        w=fixture()
        w[2]=(11<<26)|(4<<16)
        with self.assertRaisesRegex(ValueError,"original_cmp"):classify(w)
        w=fixture()
        w[6]=0x60000000
        with self.assertRaisesRegex(ValueError,"original_branch"):classify(w)
        self.assertEqual(effect(0x60000000),("logical","keep"))
        with self.assertRaisesRegex(ValueError,"original_sha"):audit(b"unverified")
    def test_private_job(self):
        wf=(Path(__file__).resolve().parents[2]/
            ".github/workflows/wii-v290-nand-input-liveness.yml").read_text()
        self.assertIn("V290_NAND_INPUT_AUDIT verified=1",wf)
        self.assertIn("WII_ORIGINAL_ELF_ID",wf)
        self.assertNotIn("upload-artifact",wf)
        self.assertEqual(wf.count("      - name: Remove private owner inputs"),1)

if __name__=="__main__":
    unittest.main()
