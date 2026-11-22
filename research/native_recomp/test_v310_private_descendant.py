#!/usr/bin/env python3
"""V310 synthetic-only exact, reversible 64-word descendant restoration."""
import hashlib
import struct
import unittest

from extend_private_text import NOP
from make_osinit_execparams_v28 import text_at
from restore_v310_private_descendant import TARGET,WORDS,SIZE,restore,audit

def dol(code:bytes)->bytes:
    header=bytearray(256)
    struct.pack_into(">I",header,0,256)
    struct.pack_into(">I",header,0x48,TARGET)
    struct.pack_into(">I",header,0x90,len(code))
    return bytes(header)+code

ORIGINAL=struct.pack(">I",0x38600001)*(WORDS-1)+struct.pack(">I",0x4e800020)
OWNER=dol(ORIGINAL)
REDUCED=dol(NOP*WORDS)
ELF=b"synthetic symbols, no game material"

class Tests(unittest.TestCase):
    def test_exact_private_restoration_and_roundtrip(self):
        restored,row=restore(OWNER,REDUCED)
        self.assertEqual(text_at(restored,TARGET,SIZE),ORIGINAL)
        self.assertEqual(len(restored),len(REDUCED))
        self.assertEqual(restored[:256],REDUCED[:256])
        self.assertIn("words=64 same=0 nop=64 roundtrip=1 candidate=1",row)

    def test_foreign_instruction_or_partial_original_rejected(self):
        foreign=bytearray(REDUCED)
        foreign[-4:]=struct.pack(">I",0x38600007)
        with self.assertRaisesRegex(ValueError,"foreign_fixture_word"):
            restore(OWNER,bytes(foreign))
        partial=bytearray(REDUCED)
        partial[-4:]=ORIGINAL[-4:]
        with self.assertRaisesRegex(ValueError,"not_exact_nop_fixture"):
            restore(OWNER,bytes(partial))

    def test_missing_or_mis_sized_function_rejected(self):
        with self.assertRaisesRegex(ValueError,"function_size"):
            restore(OWNER,REDUCED,SIZE-4)
        with self.assertRaises(ValueError):
            restore(OWNER,dol(NOP*(WORDS-1)))

    def test_both_original_hashes_and_size_required(self):
        restored,row=audit(
            OWNER,ELF,REDUCED,
            dol_digest=hashlib.sha256(OWNER).hexdigest(),
            elf_digest=hashlib.sha256(ELF).hexdigest(),
            parser=lambda _:{TARGET:SIZE}
        )
        self.assertIn("roundtrip=1",row)
        self.assertEqual(text_at(restored,TARGET,SIZE),ORIGINAL)
        with self.assertRaisesRegex(ValueError,"authenticated_digest"):
            audit(OWNER,ELF,REDUCED)
        with self.assertRaisesRegex(ValueError,"function_size"):
            audit(
                OWNER,ELF,REDUCED,
                dol_digest=hashlib.sha256(OWNER).hexdigest(),
                elf_digest=hashlib.sha256(ELF).hexdigest(),
                parser=lambda _:{TARGET:SIZE-4}
            )

if __name__=="__main__":
    unittest.main()
