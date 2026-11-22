#!/usr/bin/env python3
"""V321 synthetic-only CPU-neutral AOT-entry observer regression tests."""
import shutil
import subprocess
import unittest

from derive_v321_guest_entry_probe import (
    HEAD,GUARD71,GUARD112,TARGETS,MARKER,INJECTION,patch
)

SOURCE=(
    "#include <cstdint>\n#include <iostream>\n"
    "struct CPUContext{};\n"
    "bool v250_candidate_mode=true;\n"
    "unsigned v250_nand_seen=1u;\n"
    "bool open71_trace(uint32_t,CPUContext&){return false;}\n"
    "void observe_async(unsigned post111_open,unsigned post110_chosen){\n"
    "  "+GUARD112+"false){} (void)post111_open;(void)post110_chosen;\n"
    "}\n"
    + HEAD+"\n"
    "  (void)ctx;\n"
    "  "+GUARD71+"\n"
    "}\n"
)
class Tests(unittest.TestCase):
    def test_unique_patch_preserves_every_other_source_byte(self):
        rendered=patch(SOURCE)
        self.assertEqual(rendered.replace(HEAD+INJECTION,HEAD,1),SOURCE)
        self.assertEqual(rendered.count(MARKER),1)
        self.assertEqual(rendered.count("v321_entry_mask"),3)
        self.assertIn("v250_candidate_mode&&v250_nand_seen==1u",rendered)

    def test_exact_bounded_known_targets_and_no_guest_mutation(self):
        self.assertEqual(len(TARGETS),8)
        self.assertEqual(len(set(TARGETS)),len(TARGETS))
        for pc in TARGETS:
            self.assertIn(f"0x{pc:08x}u",INJECTION)
        for dangerous in ("ctx.pc=", "ctx.gpr", "ctx.mmu", "ctx.is_running",
                          "ctx.msr", "ipc70_bus.", "ctx.lr="):
            self.assertNotIn(dangerous,INJECTION)

    def test_fail_closed_if_prior_scope_missing_or_already_added(self):
        for invalid in (
            SOURCE.replace(GUARD71,"",1),
            SOURCE.replace(GUARD112,"",1),
            SOURCE+HEAD,
            patch(SOURCE),
        ):
            with self.subTest(size=len(invalid)):
                with self.assertRaisesRegex(ValueError,"guest_entry_source_guard"):
                    patch(invalid)

    def test_synthetic_cpp_compiles(self):
        compiler=shutil.which("g++")
        if not compiler:
            self.skipTest("g++ unavailable")
        p=subprocess.run(
            [compiler,"-std=c++20","-Wall","-Wextra","-Werror",
             "-x","c++","-fsyntax-only","-"],
            input=patch(SOURCE),capture_output=True,text=True
        )
        self.assertEqual(p.returncode,0,p.stderr[:1200])

if __name__=="__main__":
    unittest.main()
