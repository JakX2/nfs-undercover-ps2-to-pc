#!/usr/bin/env python3
"""V292 original-free fixture/AOT mapping regression tests."""
import hashlib
from pathlib import Path
import struct
import unittest
from audit_v292_nand_aot_reach import (
    TARGETS,CHILD,SOURCE,word_counts,emitted,link,audit)
def fake(pc,body):
    return (f"void fun_{pc:08x}(CPUContext& ctx) {{\n"
            f"  nwii::runtime::trace_call(0x{pc:08x}, ctx);\n"
            f"  {body}\n}}\n")
class Tests(unittest.TestCase):
    def test_aot_called_vs_unmapped(self):
        cpp=fake(CHILD,f"ctx.pc = 0x{SOURCE:08x}; fun_{SOURCE:08x}(ctx);")
        cpp+=fake(SOURCE,"ctx.pc=ctx.lr;")
        cpp+="\n{0x8052fa60, 0x8052fb60, fun_8052fa60},\n"
        self.assertEqual(link(cpp),(1,0,1))
        self.assertEqual(emitted(cpp,SOURCE)["body"],1)
        self.assertEqual(emitted(cpp,CHILD)["dispatch"],1)
        un=fake(CHILD,f"ctx.pc = 0x{SOURCE:08x}; return; // bl to unmapped target")
        self.assertEqual(link(un),(1,1,0))
        self.assertEqual(emitted(un,SOURCE)["body"],0)

    def test_word_provenance_and_sha(self):
        a=struct.pack(">4I",1,2,3,4)
        c=struct.pack(">4I",1,0x60000000,0x4e800020,5)
        self.assertEqual(word_counts(a,c),dict(same=1,nop=1,blr=1,other=1))
        orig=b"wii synthetic owner-data"
        spans={pc:b"\x60\x00\x00\x00"*(n//4) for pc,n in TARGETS}
        def reader(data,pc,size):return spans[pc]
        cpp=fake(CHILD,f"ctx.pc = 0x{SOURCE:08x}; return; // bl to unmapped target")
        rows=audit(orig,orig,cpp,hashlib.sha256(orig).hexdigest(),reader)
        self.assertIn("child_original=1 source_original=1",rows[0])
        self.assertIn("source_aot=0 child_bl=1 unmapped_bl=1",rows[0])
        with self.assertRaisesRegex(ValueError,"original_sha"):
            audit(orig,orig,cpp,reader=reader)
        # A full owner DOL and a reduced fixture have intentionally
        # different lengths; a missing guest-addressed function is a
        # reported coverage gap, never treated as NOP or fabricated code.
        reduced=b"reduced"
        def missing_reader(data,pc,size):
            if data==reduced and pc==SOURCE:
                raise ValueError("missing code")
            return spans[pc]
        rows=audit(orig,reduced,cpp,hashlib.sha256(orig).hexdigest(),
                   missing_reader)
        self.assertIn("source_original=0",rows[0])
        source_row=next(x for x in rows if f"pc={SOURCE:08x}" in x)
        self.assertIn("present=0 same=0 nop=0 blr=0 other=0",source_row)

    def test_private_ci(self):
        wf=(Path(__file__).resolve().parents[2]/
            ".github/workflows/wii-v292-nand-aot-reach.yml").read_text()
        self.assertIn("V292_AOT_AUDIT verified=1",wf)
        self.assertIn("WII_ORIGINAL_ELF_ID",wf)
        self.assertNotIn("upload-artifact",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)

if __name__=="__main__":
    unittest.main()
