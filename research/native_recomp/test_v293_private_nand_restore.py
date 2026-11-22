#!/usr/bin/env python3
"""V293 original-free exact-placeholder reversible restoration tests."""
import hashlib
import struct
from pathlib import Path
import unittest
from audit_v293_private_nand_restore import TARGETS,restore,audit,classify_span
from extend_private_text import NOP
from make_osinit_execparams_v28 import text_at

def dol(reduced:bool):
    header=bytearray(256)
    content=bytearray()
    for i,pc in enumerate(TARGETS):
        struct.pack_into(">I",header,4*i,256+len(content))
        struct.pack_into(">I",header,0x48+4*i,pc)
        struct.pack_into(">I",header,0x90+4*i,16)
        body=(NOP*4 if reduced else
              struct.pack(">4I",0x38600001,0x38630001,0x38630002,0x4e800020))
        content.extend(body)
    return bytes(header+content)

class Tests(unittest.TestCase):
    def test_four_function_restoration_reversible(self):
        owner=dol(False)
        reduced=dol(True)
        sizes={pc:16 for pc in TARGETS}
        candidate,lines=restore(owner,reduced,sizes)
        self.assertEqual(len(lines),5)
        self.assertIn("owner=1 funcs=4 changed=16 total_words=16 roundtrip=1",lines[0])
        for pc in TARGETS:
            self.assertEqual(text_at(candidate,pc,16),text_at(owner,pc,16))
        self.assertEqual(len(candidate),len(reduced))

    def test_foreign_and_missing_source_rejected(self):
        owner=dol(False)
        fixture=bytearray(dol(True))
        fixture[256:260]=b"\x7c\x00\x00\x00"
        sizes={pc:16 for pc in TARGETS}
        with self.assertRaisesRegex(ValueError,"foreign_fixture_word"):
            restore(owner,bytes(fixture),sizes)
        with self.assertRaisesRegex(ValueError,"function_size"):
            restore(owner,dol(True),{TARGETS[0]:16})
        with self.assertRaisesRegex(ValueError,"fixture_not_placeholder"):
            restore(owner,owner,sizes)
        self.assertEqual(classify_span(NOP*2,NOP*2),(2,0))

    def test_both_original_digests_sha_pinned(self):
        owner=dol(False)
        fixture=dol(True)
        elf=b"synthetic PowerPC symbols, not game data"
        sizes={pc:16 for pc in TARGETS}
        candidate,lines=audit(owner,elf,fixture,
            hashlib.sha256(owner).hexdigest(),
            hashlib.sha256(elf).hexdigest(),
            lambda _:sizes)
        self.assertIn("candidate=1",lines[0])
        self.assertEqual(text_at(candidate,TARGETS[0],16),
                         text_at(owner,TARGETS[0],16))
        with self.assertRaisesRegex(ValueError,"authenticated_digest"):
            audit(owner,elf,fixture)

    def test_private_workflow(self):
        wf=(Path(__file__).resolve().parents[2]/
            ".github/workflows/wii-v293-private-nand-restore.yml").read_text()
        self.assertIn("V293_RESTORE_AUDIT verified=1",wf)
        self.assertIn("WII_ORIGINAL_ELF_ID",wf)
        self.assertNotIn("upload-artifact",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)

if __name__=="__main__":
    unittest.main()
