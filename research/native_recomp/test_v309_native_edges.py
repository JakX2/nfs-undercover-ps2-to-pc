#!/usr/bin/env python3
"""V309 original-free exact vs interior native edge linkage tests."""
import hashlib
import unittest

from analyze_v309_native_edges import HELPER,HELPER_BYTES,inspect,TARGETS

OWNER=b"sha-pinned synthetic owner"
ELF=b"synthetic ELF symbols"
PRIVATE=b"restored synthetic DOL"
WORDS=b"\x60\x00\x00\x00"*(HELPER_BYTES//4)
P0,P1,P2,P3=TARGETS
PARENT=P2-4

GEN=(f"""void AotHelper(CPUContext& ctx) {{
 nwii::runtime::trace_call(0x{HELPER:08x}, ctx);
 ctx.pc = 0x{P0:08x}; call_0(ctx);
 ctx.pc = 0x{P1:08x}; call_1(ctx);
 ctx.pc = 0x{P2:08x}; return; // bl to unmapped target
 ctx.pc = 0x{P3:08x}; call_3(ctx);
}}
void Target0(CPUContext& ctx) {{
 nwii::runtime::trace_call(0x{P0:08x}, ctx);
}}
void Parent2(CPUContext& ctx) {{
 nwii::runtime::trace_call(0x{PARENT:08x}, ctx);
}}
"""
+f"{{0x{P0:08x}, 0x12345678,}}\n"
+f"{{0x{PARENT:08x}, 0x12345678,}}\n")

def reader(data,pc,size):
    if pc!=HELPER or size!=HELPER_BYTES:
        raise ValueError("unexpected input")
    return WORDS if data in (OWNER,PRIVATE) else b""

def run(generated=GEN,private=PRIVATE):
    return inspect(
        OWNER,ELF,private,generated,
        dol_digest=hashlib.sha256(OWNER).hexdigest(),
        elf_digest=hashlib.sha256(ELF).hexdigest(),
        parser=lambda _: {P0:16,P1:16,PARENT:64,P3:16},
        reader=reader
    )

class Tests(unittest.TestCase):
    def test_interior_dispatch_not_confused_with_parent(self):
        rows=run()
        self.assertIn("targets=4 callsite=4",rows[0])
        self.assertIn("direct=3 unmapped=1",rows[0])
        self.assertIn("target_dispatch=1 parent_dispatch=2",rows[0])
        self.assertIn("kind=interior",rows[3])
        self.assertIn("target_dispatch=0 parent_body=1 parent_dispatch=1",rows[3])
        self.assertIn("unmapped=1",rows[3])

    def test_wrong_original_refused(self):
        def wrong(data,pc,size):
            return WORDS if data==OWNER else b"\xff"*size
        with self.assertRaisesRegex(ValueError,"helper_original"):
            inspect(
                OWNER,ELF,PRIVATE,GEN,
                dol_digest=hashlib.sha256(OWNER).hexdigest(),
                elf_digest=hashlib.sha256(ELF).hexdigest(),
                parser=lambda _:{P0:16},reader=wrong
            )

    def test_missing_native_helper_rejected(self):
        with self.assertRaisesRegex(ValueError,"helper_not_emitted"):
            run("void NoTrace(CPUContext& ctx) {}")

if __name__=="__main__":
    unittest.main()
