#!/usr/bin/env python3
"""V302 source-only restoration tests; no proprietary game bytes."""
import hashlib
from pathlib import Path
import struct
import tempfile
import unittest

from extend_private_text import NOP, unpack
from make_osinit_execparams_v28 import text_at
from restore_v302_private_helper import TARGET, audit, restore

BASE=TARGET-0x64
BODY=struct.pack(">4I",0x38600001,0x38630001,0x38630002,0x4e800020)
PREFIX=NOP*25

def dol(data:bytes)->bytes:
    head=bytearray(256)
    struct.pack_into(">I",head,0,256)
    struct.pack_into(">I",head,0x48,BASE)
    struct.pack_into(">I",head,0x90,len(data))
    return bytes(head)+data

OWNER=dol(PREFIX+BODY)
ABSENT=dol(PREFIX)
PLACEHOLDER=dol(PREFIX+NOP*4)
FOREIGN=dol(PREFIX+struct.pack(">4I",1,2,3,4))
ELF=b"synthetic private symbol table"

class Tests(unittest.TestCase):
    def test_missing_span_extended_and_original_recovered(self):
        candidate,line=restore(OWNER,ABSENT,len(BODY))
        self.assertEqual(text_at(candidate,TARGET,len(BODY)),BODY)
        self.assertIn("words=4 present=0 same=0 nop=0 extended=1",line)
        self.assertEqual(unpack(candidate)[0][3][:len(PREFIX)],PREFIX)
        self.assertEqual(len(ABSENT)+len(BODY),len(candidate))

    def test_nop_span_restored_without_extension(self):
        candidate,line=restore(OWNER,PLACEHOLDER,len(BODY))
        self.assertEqual(text_at(candidate,TARGET,len(BODY)),BODY)
        self.assertIn("present=1 same=0 nop=4 extended=0",line)
        self.assertEqual(len(candidate),len(PLACEHOLDER))
        self.assertEqual(candidate[:256],PLACEHOLDER[:256])

    def test_foreign_and_already_original_refused(self):
        with self.assertRaisesRegex(ValueError,"foreign_fixture_word"):
            restore(OWNER,FOREIGN,len(BODY))
        with self.assertRaisesRegex(ValueError,"helper_already_original"):
            restore(OWNER,OWNER,len(BODY))
        with self.assertRaisesRegex(ValueError,"helper_size"):
            restore(OWNER,ABSENT,0)

    def test_both_owner_digests_mandatory(self):
        candidate,row=audit(
            OWNER,ELF,ABSENT,
            hashlib.sha256(OWNER).hexdigest(),
            hashlib.sha256(ELF).hexdigest(),
            lambda _: {TARGET:len(BODY)}
        )
        self.assertIn("candidate=1",row)
        self.assertEqual(text_at(candidate,TARGET,len(BODY)),BODY)
        with self.assertRaisesRegex(ValueError,"authenticated_digest"):
            audit(OWNER,ELF,ABSENT)

if __name__=="__main__":
    unittest.main()
