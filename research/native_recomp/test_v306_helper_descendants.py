#!/usr/bin/env python3
"""V306 original-free four-descendant AOT coverage tests."""
import hashlib
import unittest

from analyze_v306_helper_descendants import TARGETS,inspect

ORIGINAL=b"\x38\x60\x00\x01"*4
NOP=b"\x60\x00\x00\x00"*4
FOREIGN=b"\x38\x60\x00\x02"*4
OWNER=b"synthetic-owner-only"
ELF=b"synthetic-symbol-index"
FIXTURE=b"synthetic-reduced-dol"
CPP=("\n".join(
    f"void code_{pc:08x}(CPUContext& ctx) {{\n"
    f"nwii::runtime::trace_call(0x{pc:08x}, ctx);\n}}\n"
    for pc in TARGETS[:2]
)+"\n"+ "\n".join(
    f"{{0x{pc:08x}, 0x12345678,}}" for pc in TARGETS[:2]
))

def reader(data,pc,size):
    if size!=len(ORIGINAL):
        raise ValueError("unexpected_size")
    if data==OWNER:
        return ORIGINAL
    if data==FIXTURE:
        idx=TARGETS.index(pc)
        if idx==0:
            return ORIGINAL
        if idx==1:
            return NOP
        if idx==2:
            raise ValueError("unmapped fixture")
        return FOREIGN
    raise ValueError("unexpected data")

def sample(**kwargs):
    return inspect(
        OWNER,ELF,FIXTURE,CPP,
        dol_digest=hashlib.sha256(OWNER).hexdigest(),
        elf_digest=hashlib.sha256(ELF).hexdigest(),
        parser=lambda _: {x:len(ORIGINAL) for x in TARGETS},
        reader=reader,**kwargs
    )

class Tests(unittest.TestCase):
    def test_exact_nop_missing_and_foreign(self):
        rows=sample()
        self.assertEqual(len(rows),5)
        self.assertIn("targets=4 exact=1 emitted=2 dispatch=2",rows[0])
        self.assertIn("missing=1 partial=2",rows[0])
        self.assertIn("present=1 same=4 nop=0",rows[1])
        self.assertIn("present=1 same=0 nop=4",rows[2])
        self.assertIn("present=0 same=0 nop=0",rows[3])
        self.assertIn("present=1 same=0 nop=0",rows[4])
        self.assertIn("other=4",rows[4])

    def test_original_authenticity_mandatory(self):
        with self.assertRaisesRegex(ValueError,"authenticated_digest"):
            inspect(OWNER,ELF,FIXTURE,CPP)
        with self.assertRaisesRegex(ValueError,"fixture_geometry"):
            inspect(
                OWNER,ELF,FIXTURE,"",
                hashlib.sha256(OWNER).hexdigest(),
                hashlib.sha256(ELF).hexdigest()
            )

    def test_missing_symbol_fails_closed(self):
        with self.assertRaisesRegex(ValueError,"function_size"):
            inspect(
                OWNER,ELF,FIXTURE,CPP,
                hashlib.sha256(OWNER).hexdigest(),
                hashlib.sha256(ELF).hexdigest(),
                parser=lambda _: {TARGETS[0]:16},reader=reader
            )

if __name__=="__main__":
    unittest.main()
