#!/usr/bin/env python3
"""Source-only differential analysis of synthetic AOT callback functions."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from audit_v251_callback_generated_diff import compare,functions
from derive_v251_callback_generated_diff_runner import derive as runner,STAGE,PATTERN

HERE=Path(__file__).resolve().parent

def sample(addr:int,tag:str)->str:
    return (
        f"void f_{addr:08x}(CPUContext& ctx) {{\n"
        f"    if (nwii::runtime::g_trace_calls) "
        f"nwii::runtime::trace_call(0x{addr:08x}, ctx);\n"
        f"    // synthetic {tag}\n"
        "    ctx.inst_count++;\n"
        "}\n\n"
    )

class V251(unittest.TestCase):
    def test_mutation_only_in_two_original_callback_bodies(self):
        ids=[0x804f0e04,0x8051e06c,0x804f1e2c,0x805190c0,0x8051982c]
        old="".join(sample(addr,"baseline") for addr in ids)
        new="".join(sample(addr,"restored" if addr in ids[:2] else "baseline") for addr in ids)
        row=compare(old,new)
        self.assertEqual(row,
            "V251_AOT_DIFF parsed=1 cb=1 nand=1 ipc=1 isfs=1 async=1 changed=0 new=0 removed=0")
        self.assertIsNotNone(re.fullmatch(PATTERN,row))
        self.assertEqual(len(functions(old)),len(ids))
        altered=new.replace("synthetic baseline","synthetic altered")
        self.assertIn("changed=3",compare(old,altered))

    def test_fail_closed_on_missing_or_duplicate_entry(self):
        one=sample(0x804f0e04,"baseline")
        with self.assertRaises(ValueError):compare(one,one)
        both=sample(0x8051e06c,"nand")+one
        with self.assertRaises(ValueError):functions(both+both)
        with self.assertRaises(ValueError):compare("",both)

    def test_owner_pipeline_preserves_private_output(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        self.assertIn('V249_SC_AUTH_CALLBACK_LINK verified=1',script)
        self.assertIn('V251_SC_CALLBACK_DIFF verified=1',script)
        self.assertIn('audit_v251_callback_generated_diff.py',script)
        self.assertIn('> "$work/v251-diff.log" 2>&1',script)
        self.assertNotIn("cat $work",STAGE)
        self.assertNotIn('upload-artifact',STAGE)
        wf=(HERE.parents[1]/".github/workflows/wii-v251-callback-generated-diff.yml").read_text()
        for key in ("run_v251_callback_generated_diff.sh",
                    "test_v251_callback_generated_diff.py",
                    "V251_SC_CALLBACK_DIFF verified=1"):
            self.assertIn(key,wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)
        with tempfile.TemporaryDirectory() as temp:
            for name,text in (
                ("runner.sh",script),
                ("wrapper.sh",(HERE/"run_v251_callback_generated_diff.sh").read_text())
            ):
                path=Path(temp)/name;path.write_text(text,encoding="utf-8")
                subprocess.run(["bash","-n",str(path)],check=True)

if __name__=="__main__":
    unittest.main()
