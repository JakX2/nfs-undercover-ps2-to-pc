#!/usr/bin/env python3
"""V317 original-free synthetic coverage and privacy tests."""
import hashlib
import unittest

from audit_v317_descendant_edges import HELPER,HELPER_SIZE,TARGETS,inspect

OWNER=b"test owner DOL"
ELF=b"test owner ELF"
CANDIDATE=b"test private candidate"
BODY=b"\x60\x00\x00\x00"*(HELPER_SIZE//4)
E0,E1,E2,E3,E4=TARGETS

GEN=(
    f"void Helper(CPUContext& ctx) {{\n"
    f"nwii::runtime::trace_call(0x{HELPER:08x}, ctx);\n"
    f"ctx.pc = 0x{E0:08x}; ios_request(ctx);\n"
    f"ctx.pc = 0x{E1:08x}; allocator_tail(ctx);\n"
    f"ctx.pc = 0x{E2:08x}; return; // bl to unmapped target\n"
    f"ctx.pc = 0x{E3:08x}; interior_a(ctx);\n"
    f"ctx.pc = 0x{E4:08x}; interior_b(ctx);\n"
    f"}}\n"
    f"void Req(CPUContext& ctx) {{ nwii::runtime::trace_call(0x{E0:08x}, ctx); }}\n"
    f"{{0x{E0:08x}, 0x12345678,}}\n"
)

def reader(raw,pc,size):
    if pc!=HELPER or size!=HELPER_SIZE:
        raise ValueError("untrusted fixture")
    return BODY if raw in (OWNER,CANDIDATE) else b""

def run(code=GEN,read=reader):
    return inspect(
        OWNER,ELF,CANDIDATE,code,
        dol_digest=hashlib.sha256(OWNER).hexdigest(),
        elf_digest=hashlib.sha256(ELF).hexdigest(),
        symbol_parser=lambda _:{x:16 for x in TARGETS},
        reader=read
    )

class Tests(unittest.TestCase):
    def test_five_authenticated_call_edges_and_unmapped(self):
        rows=run()
        self.assertEqual(len(rows),6)
        self.assertIn("targets=5 site=5 direct=4 unmapped=1 dispatch=1",rows[0])
        self.assertIn(f"pc={E2:08x} kind=exact original=1 site=1 direct=0 unmapped=1",rows[3])

    def test_no_original_or_generated_bytes_exposed(self):
        out="\n".join(run())
        self.assertNotIn("test owner DOL",out)
        self.assertNotIn("nwii::runtime",out)
        self.assertNotIn("60000000",out)

    def test_wrong_owner_or_candidate_fails(self):
        with self.assertRaisesRegex(ValueError,"authenticated_digest"):
            inspect(OWNER,ELF,CANDIDATE,GEN)
        def changed(raw,pc,size):
            return b"\xff"*size if raw==CANDIDATE else BODY
        with self.assertRaisesRegex(ValueError,"authentic_helper"):
            run(read=changed)

    def test_missing_native_body_fails_closed(self):
        with self.assertRaisesRegex(ValueError,"missing_body"):
            run("void unrelated(CPUContext& ctx) {}")

if __name__=="__main__":
    unittest.main()
