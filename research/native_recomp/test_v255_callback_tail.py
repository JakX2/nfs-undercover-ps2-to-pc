#!/usr/bin/env python3
"""V255 original-free generated-function/tail separation regression."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from audit_v255_callback_tail import compare,body_only
from derive_v255_callback_tail_runner import derive as runner, PATTERN, PASS, STAGE
HERE=Path(__file__).resolve().parent

CB=0x804f0e04
NAND=0x8051e06c
ISFS=0x804f1e2c
IPC=0x805190c0
ASYNC=0x8051982c
LAST=0x8054b4b4

def sample(pc:int,tag:str)->str:
    return (f"void f_{pc:08x}(CPUContext& ctx) {{\n"
            '  // quoted brace in comment: }\n'
            '  const char *text = "{ escaped }";\n'
            '  if (ctx.inst_count > 0) { ctx.inst_count++; }\n'
            f"  nwii::runtime::trace_call(0x{pc:08x}, ctx);\n"
            f"  // original-free {tag}\n"
            "}\n\n")

class V255(unittest.TestCase):
    def prepare(self,last_tag="base",tail="original"):
        codes=[CB,NAND,ISFS,IPC,ASYNC,LAST]
        b="".join(sample(k,"base") for k in codes)
        a="".join(sample(k,"new" if k in (CB,NAND) else
                         last_tag if k==LAST else "base") for k in codes)
        b+="// synthetic generated registration "+tail+"\n"
        a+="// synthetic generated registration restored\n"
        return b,a

    def test_last_function_body_unchanged_but_suffix_changed(self):
        before,after=self.prepare()
        row=compare(before,after)
        self.assertEqual(row,
            "V255_AOT_TAIL parsed=1 last=1 pc=8054b4b4 body_same=1 tail_diff=1 controls=1 extras=1")
        self.assertIsNotNone(re.fullmatch(PASS,row))
        self.assertEqual(body_only(sample(LAST,"base")),
                         sample(LAST,"base").rstrip())
        row2=compare(*self.prepare(last_tag="changed"))
        self.assertIn("body_same=0 tail_diff=1",row2)
        self.assertIsNone(re.fullmatch(PASS,row2))
        self.assertIsNotNone(re.fullmatch(PATTERN,row2))

    def test_fail_closed_on_missing_or_changed_control(self):
        before,after=self.prepare()
        with self.assertRaises(ValueError):compare(before,before)
        with self.assertRaises(ValueError):compare("",after)
        with self.assertRaises(ValueError):
            compare(before,after.replace("// original-free base",
                                         "// original-free altered",1))
        with self.assertRaises(ValueError):body_only("void f(CPUContext& ctx) {")
        with self.assertRaises(ValueError):body_only("broken")

    def test_owner_runner_safety_and_cleanup(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text(encoding="utf-8"))
        for m in ("audit_v255_callback_tail.py",
                  "V253_SC_AOT_OTHER verified=1",
                  "V255_SC_AOT_TAIL verified=1",
                  '"$work/generated/output.cpp"',
                  '"$work/generated-v248/output.cpp"'):
            self.assertIn(m,script)
        self.assertNotIn('cat "$work',STAGE)
        self.assertNotIn("upload-artifact",STAGE)
        wf=(HERE.parents[1]/".github/workflows/wii-v255-callback-tail.yml").read_text()
        for m in ("run_v255_callback_tail.sh","test_v255_callback_tail.py",
                  "V255_SC_AOT_TAIL verified=1"):
            self.assertIn(m,wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)
        with tempfile.TemporaryDirectory() as d:
            for name,content in (("runner",script),("wrapper",(HERE/"run_v255_callback_tail.sh").read_text())):
                path=Path(d)/name;path.write_text(content,encoding="utf-8")
                subprocess.run(["bash","-n",str(path)],check=True)

if __name__=="__main__":
    unittest.main()
