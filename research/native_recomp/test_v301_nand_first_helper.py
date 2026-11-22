#!/usr/bin/env python3
"""V301 original-free NAND first-helper fixture and AOT provenance tests."""
import hashlib
import unittest

from audit_v292_nand_aot_reach import word_counts
from analyze_v301_nand_first_helper import TARGET, CALLER, analyze

ORIGINAL = b"\x38\x60\x00\x01"*4
REDUCED = b"\x60\x00\x00\x00"*4
ELF = b"synthetic symbol records"
CPP = f'''void First(CPUContext& ctx) {{
  nwii::runtime::trace_call(0x{CALLER:08x}, ctx);
  ctx.pc = 0x{TARGET:08x}; nwii::runtime::AotHelper(ctx);
}}
void Second(CPUContext& ctx) {{
  nwii::runtime::trace_call(0x{TARGET:08x}, ctx);
}}
static auto dispatch = {{0x{TARGET:08x}, 0x12345678,}};
'''

def reader(data, pc, size):
    if pc != TARGET or size != len(ORIGINAL):
        raise ValueError("unexpected_source")
    return data

def fixture(data=ORIGINAL, generated=CPP):
    return analyze(
        ORIGINAL,ELF,data,generated,
        dol_sha=hashlib.sha256(ORIGINAL).hexdigest(),
        elf_sha=hashlib.sha256(ELF).hexdigest(),
        parser=lambda _: {TARGET:len(ORIGINAL)},
        reader=reader
    )

class Tests(unittest.TestCase):
    def test_original_helper_and_native_dispatch(self):
        row=fixture()
        self.assertIn("pc=804f2064 words=4 present=1 same=4 nop=0",row)
        self.assertIn("body=1 dispatch=1 caller=1 unmapped=0 direct=1",row)

    def test_placeholder_helper_detected(self):
        row=fixture(REDUCED)
        self.assertIn("same=0 nop=4 blr=0 other=0",row)
        self.assertIn("body=1 dispatch=1",row)
        self.assertEqual(word_counts(ORIGINAL,REDUCED)["nop"],4)

    def test_no_helper_body_not_confused_with_success(self):
        cpp=CPP.replace(
            f"nwii::runtime::trace_call(0x{TARGET:08x}, ctx);",
            "nwii::runtime::trace_call(0x80510000, ctx);"
        ).replace(f"0x{TARGET:08x}, 0x12345678,","0x80510000, 0x12345678,")
        self.assertIn("body=0 dispatch=0",fixture(REDUCED,cpp))

    def test_invalid_original_digest_and_size_rejected(self):
        with self.assertRaisesRegex(ValueError,"owner_sha"):
            analyze(ORIGINAL,ELF,REDUCED,CPP,dol_sha="0"*64)
        with self.assertRaisesRegex(ValueError,"helper_size"):
            analyze(ORIGINAL,ELF,REDUCED,CPP,
                    dol_sha=hashlib.sha256(ORIGINAL).hexdigest(),
                    elf_sha=hashlib.sha256(ELF).hexdigest(),
                    parser=lambda _: {TARGET:0},reader=reader)

if __name__=="__main__":
    unittest.main()
