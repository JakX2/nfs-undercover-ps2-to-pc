#!/usr/bin/env python3
"""Original-free V127 OSInit tail audit classification and bounded privacy checks."""
import struct
import unittest
from pathlib import Path
from diagnose_v127_osinit_tail import START,SIZE,SYNTHETIC,words,classify,report
from make_osinit_execparams_v28 import SC,BLR,NOP
HERE=Path(__file__).resolve().parent

def fixture(payload):
    blob=bytearray(256+SIZE)
    struct.pack_into(">I",blob,0,256)
    struct.pack_into(">I",blob,0x48,START)
    struct.pack_into(">I",blob,0x90,SIZE)
    blob[256:]=struct.pack(">IIII",*payload)
    return bytes(blob)

class V127Window(unittest.TestCase):
    def test_synthetic_and_original_word_classes(self):
        self.assertEqual(SIZE,16)
        self.assertEqual(SYNTHETIC,(SC,BLR,NOP,NOP))
        original=(0x48000001,0x60000000,0x4e800020,0x44000002)
        got=classify(words(fixture(original)),words(fixture(SYNTHETIC)))
        self.assertEqual(got["placeholder"],1)
        self.assertEqual(got["changed"],1)
        self.assertEqual(got["first_branch"],1)
        self.assertEqual(got["branch_count"],1)
        self.assertEqual(got["return_count"],1)
        self.assertEqual(got["syscall_count"],1)
        message=report(got)
        self.assertIn("V127_OSINIT_WINDOW placeholder=1 changed=1",message)
        self.assertNotIn("48000001",message)
    def test_deny_bad_layout(self):
        with self.assertRaises(ValueError):
            classify((SC,BLR,NOP),SYNTHETIC)
        bad=bytearray(fixture(SYNTHETIC))
        struct.pack_into(">I",bad,0x90,SIZE-4)
        with self.assertRaises(ValueError):
            words(bytes(bad))
    def test_no_private_instruction_publication(self):
        s=(HERE/"diagnose_v127_osinit_tail.py").read_text()
        self.assertIn("hashlib.sha256(original).hexdigest()!=ORIGINAL_SHA",s)
        self.assertNotIn("print(original)",s)
        self.assertNotIn("print(words(",s)
        self.assertIn("V127_OSINIT_WINDOW result=failed",s)
if __name__=="__main__":
    unittest.main()
