#!/usr/bin/env python3
"""V253 original-free tests for safe extra AOT function classification."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from audit_v253_callback_other import classify
from derive_v253_callback_other_runner import derive as runner, PATTERN, STAGE
HERE=Path(__file__).resolve().parent

def sample(pc:int,name:str)->str:
    return (f"void f_{pc:08x}(CPUContext& ctx) {{\n"
            f"  nwii::runtime::trace_call(0x{pc:08x}, ctx);\n"
            f"  // original-free {name}\n"
            "  ctx.inst_count++;\n"
            "}\n\n")

CB=0x804f0e04
NAND=0x8051e06c
ISFS=0x804f1e2c
IPC=0x805190c0
ASYNC=0x8051982c

class V253(unittest.TestCase):
    def test_one_extra_callback_internal_entry_is_classified(self):
        near=CB+0x20
        codes=[CB,near,NAND,ISFS,IPC,ASYNC]
        before="".join(sample(k,"base") for k in codes)
        after="".join(sample(k,"new" if k in (CB,near,NAND) else "base") for k in codes)
        row=classify(before,after)
        self.assertEqual(row,
            "V253_AOT_OTHER parsed=1 count=1 pc=804f0e24 in_cb=1 in_nand=0 near_cb=1 near_nand=0 last=0 same_len=0 controls=1 restored=1")
        self.assertIsNotNone(re.fullmatch(PATTERN,row))
        other=CB+0x400
        codes=[CB,NAND,ISFS,IPC,ASYNC,other]
        before="".join(sample(k,"base") for k in codes)
        after="".join(sample(k,"new" if k in (CB,NAND,other) else "base") for k in codes)
        row=classify(before,after)
        self.assertIn("last=1",row)
        self.assertIn(f"pc={other:08x}",row)

    def test_rejects_false_proofs_or_changed_controls(self):
        codes=[CB,NAND,ISFS,IPC,ASYNC]
        before="".join(sample(k,"base") for k in codes)
        after="".join(sample(k,"new" if k in (CB,NAND) else "base") for k in codes)
        self.assertIn("count=0 pc=00000000",classify(before,after))
        with self.assertRaises(ValueError):classify(before,before)
        with self.assertRaises(ValueError):
            classify(before,after.replace(f"// original-free base\n  ctx.inst_count++;\n}}\n\n",
                  "// original-free changed\n  ctx.inst_count++;\n}\n\n",1))
        with self.assertRaises(ValueError):classify("",after)

    def test_private_owner_pipeline_and_cleanup(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text(encoding="utf-8"))
        for s in ("audit_v253_callback_other.py",
                  "V251_SC_CALLBACK_DIFF verified=1",
                  "V253_SC_AOT_OTHER verified=1",
                  '"$work/generated/output.cpp"',
                  '"$work/generated-v248/output.cpp"'):
            self.assertIn(s,script)
        self.assertNotIn('cat "$work',STAGE)
        self.assertNotIn("upload-artifact",STAGE)
        wf=(HERE.parents[1]/".github/workflows/wii-v253-callback-other.yml").read_text()
        for s in ("run_v253_callback_other.sh",
                  "test_v253_callback_other.py",
                  "V253_SC_AOT_OTHER verified=1"):
            self.assertIn(s,wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)
        with tempfile.TemporaryDirectory() as d:
            for name,text in (("runner",script),("wrapper",(HERE/"run_v253_callback_other.sh").read_text(encoding="utf-8"))):
                path=Path(d)/name;path.write_text(text,encoding="utf-8")
                subprocess.run(["bash","-n",str(path)],check=True)

if __name__=="__main__":
    unittest.main()
