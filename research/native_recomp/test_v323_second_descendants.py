#!/usr/bin/env python3
"""V323 synthetic-only exact/interior/placeholder NAND source coverage tests."""
import hashlib
import unittest

from analyze_v323_second_descendants import TARGETS,inspect

OWNER=b"synthetic private owner DOL"
ELF=b"synthetic private ELF"
FIXTURE=b"synthetic reduced V310 candidate"
WORDS=b"\x38\x60\x00\x01"*4
NOP=b"\x60\x00\x00\x00"*4
OTHER=b"\x38\x60\x00\x02"*4

# The first two known targets have direct native AOT, and the fourth
# has a special interior-target dispatch even without a parent entry.
CPP=("\n".join(
    f"void code_{pc:08x}(CPUContext& ctx) {{\n"
    f"nwii::runtime::trace_call(0x{pc:08x}, ctx);\n}}\n"
    for pc in (TARGETS[0],TARGETS[1],TARGETS[3])
)+"\n"+ "\n".join(
    f"{{0x{pc:08x}, 0x12345678,}}" for pc in (TARGETS[0],TARGETS[1],TARGETS[3])
))
PARENT=TARGETS[3]-4

def reader(raw,pc,size):
    if size!=len(WORDS):
        raise ValueError("invalid read window")
    if raw==OWNER:
        return WORDS
    if raw!=FIXTURE:
        raise ValueError("wrong image")
    if pc==TARGETS[0]:
        return WORDS
    if pc==TARGETS[1]:
        return NOP
    if pc==TARGETS[2]:
        raise ValueError("physically absent")
    if pc==TARGETS[3]:
        return WORDS
    return OTHER

def sample(**kwargs):
    sizes={pc:len(WORDS) for pc in TARGETS}
    del sizes[TARGETS[3]]
    sizes[PARENT]=len(WORDS)+4
    return inspect(
        OWNER,ELF,FIXTURE,CPP,
        dol_digest=hashlib.sha256(OWNER).hexdigest(),
        elf_digest=hashlib.sha256(ELF).hexdigest(),
        parser=lambda _:sizes,reader=reader,**kwargs
    )

class Tests(unittest.TestCase):
    def test_one_missing_one_nop_one_foreign_and_interior(self):
        rows=sample()
        self.assertEqual(len(rows),6)
        self.assertIn(
            "owner=1 targets=5 original=2 missing=1 partial=2 "
            "unknown=0 body=3 dispatch=3",rows[0]
        )
        self.assertIn("kind=exact",rows[1])
        self.assertIn("present=1 same=4 nop=0",rows[1])
        self.assertIn("present=1 same=0 nop=4",rows[2])
        self.assertIn("present=0 same=0 nop=0",rows[3])
        self.assertIn("kind=interior base=%08x offset=1 words=4" % PARENT,rows[4])
        self.assertIn("original=1 body=1 dispatch=1",rows[4])
        self.assertIn("other=4 original=0 body=0 dispatch=0",rows[5])

    def test_hashes_and_bounded_private_inputs_fail_closed(self):
        with self.assertRaisesRegex(ValueError,"authenticated_digest"):
            inspect(OWNER,ELF,FIXTURE,CPP)
        with self.assertRaisesRegex(ValueError,"private_geometry"):
            inspect(OWNER,ELF,b"",CPP,
                    dol_digest=hashlib.sha256(OWNER).hexdigest(),
                    elf_digest=hashlib.sha256(ELF).hexdigest())

    def test_unknown_symbol_does_not_claim_original_code(self):
        rows=inspect(
            OWNER,ELF,FIXTURE,CPP,
            dol_digest=hashlib.sha256(OWNER).hexdigest(),
            elf_digest=hashlib.sha256(ELF).hexdigest(),
            parser=lambda _: {TARGETS[0]:16},reader=reader
        )
        self.assertIn("original=1 missing=0 partial=0 unknown=4",rows[0])
        self.assertIn("kind=unknown",rows[2])
        self.assertIn("words=0 present=0",rows[2])

    def test_no_proprietary_words_or_filenames_in_output(self):
        text="\n".join(sample())
        for fragment in ("synthetic private owner","synthetic reduced","nwii::runtime",
                         "0x38600001"):
            self.assertNotIn(fragment,text)

if __name__=="__main__":
    unittest.main()
