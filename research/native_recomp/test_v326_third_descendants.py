#!/usr/bin/env python3
"""V326 original-free nine-callee authenticity and span tests."""
import hashlib
import unittest

from analyze_v326_third_descendants import TARGETS,inspect

OWNER=b"synthetic only Wii original"
ELF=b"synthetic only ELF symbols"
REDUCED=b"synthetic only restored fixture"
ORIGINAL=b"\x38\x60\x00\x01"*4
NOP=b"\x60\x00\x00\x00"*4

CPP=(
    "void first(CPUContext& ctx) {\n"
    f"nwii::runtime::trace_call(0x{TARGETS[0]:08x}, ctx);\n}}\n"
    f"{{0x{TARGETS[0]:08x}, 0x12345678,}}\n"
    "void second(CPUContext& ctx) {\n"
    f"nwii::runtime::trace_call(0x{TARGETS[2]:08x}, ctx);\n}}\n"
    f"{{0x{TARGETS[2]:08x}, 0x12345678,}}\n"
)

def reader(data,pc,n):
    if n!=len(ORIGINAL):
        raise ValueError("unknown window")
    if data==OWNER:
        return ORIGINAL
    if data!=REDUCED:
        raise ValueError("unknown image")
    if pc==TARGETS[1]:
        return NOP
    if pc==TARGETS[4]:
        raise ValueError("span omitted")
    return ORIGINAL

def sample(symbols=None):
    return inspect(
        OWNER,ELF,REDUCED,CPP,
        dol_digest=hashlib.sha256(OWNER).hexdigest(),
        elf_digest=hashlib.sha256(ELF).hexdigest(),
        parser=(lambda _:symbols or {x:16 for x in TARGETS}),
        reader=reader
    )

class Tests(unittest.TestCase):
    def test_nine_distinct_authenticated_targets_with_bounded_output(self):
        self.assertEqual(len(TARGETS),9)
        self.assertEqual(len(set(TARGETS)),9)
        lines=sample()
        self.assertEqual(len(lines),10)
        self.assertIn(
            "owner=1 targets=9 original=7 missing=1 partial=1 "
            "unknown=0 body=2 dispatch=2",lines[0]
        )
        self.assertIn("pc=8051ad3c kind=exact",lines[2])
        self.assertIn("same=0 nop=4",lines[2])
        self.assertIn("present=0",lines[5])
        self.assertNotIn("synthetic only", "\n".join(lines))
        self.assertNotIn("nwii::runtime", "\n".join(lines))

    def test_unknown_geometry_not_fabricated(self):
        lines=sample({TARGETS[0]:16})
        self.assertIn("original=1 missing=0 partial=0 unknown=8",lines[0])
        self.assertIn("kind=unknown base=00000000",lines[2])

    def test_authenticity_and_target_controls(self):
        with self.assertRaisesRegex(ValueError,"authenticated_digest"):
            inspect(OWNER,ELF,REDUCED,CPP)
        with self.assertRaisesRegex(ValueError,"target_geometry"):
            from analyze_v323_second_descendants import inspect as prior
            prior(
                OWNER,ELF,REDUCED,CPP,
                dol_digest=hashlib.sha256(OWNER).hexdigest(),
                elf_digest=hashlib.sha256(ELF).hexdigest(),
                targets=(TARGETS[0],TARGETS[0]),
                prefix="V326",depth="THIRD",parser=lambda _: {},
                reader=reader
            )

if __name__=="__main__":
    unittest.main()
