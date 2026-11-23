#!/usr/bin/env python3
"""V342: generate the complete public NAND observer harness without game assets.

The owner-original pipeline contains many individually tested derivations.
Exercise the actual source-only V77 -> V289 -> V296 -> V298 -> V340 -> V321
sequence before waiting for private ELF/AOT compilation. Do not print any
derived source text or original-game contents.
"""
from __future__ import annotations
from pathlib import Path
import subprocess
import shutil
import os
import sys
import tempfile
import unittest

from derive_v296_service_harness import patch as service
from derive_v298_scope_reply_observer import (
    patch as scope, ack_mmio_seam, ACK_MMIO_OLD, ACK_MMIO_NEW,
    submit_mmio_seam,
)
from derive_v340_nand_mmio_probe import patch as mmio
from derive_v352_nand_mailbox_route import patch as mailbox_route
from derive_v321_guest_entry_probe import patch as entry

HERE=Path(__file__).resolve().parent
SOURCE=HERE/"test_start_to_ipc_ack_v77.cpp"
V244=HERE/"derive_v244_sc_callback_link_harness.py"
V289=HERE/"derive_v289_nand_entry_r3_harness.py"

class Tests(unittest.TestCase):
    def test_full_original_free_source_derivation_chain(self):
        with tempfile.TemporaryDirectory(prefix="v342-public-") as td:
            prior=Path(td)/"v244.cpp"
            staged=Path(td)/"v289.cpp"
            self.assertTrue(SOURCE.is_file() and V244.is_file() and V289.is_file())
            try:
                staged244=subprocess.run(
                    [sys.executable,str(V244),str(SOURCE),str(prior)],
                    capture_output=True,text=True,timeout=180,
                    check=False,
                )
            except subprocess.TimeoutExpired:
                self.fail("V342_V244_DERIVE kind=timeout")
            self.assertEqual(staged244.returncode,0,
                             "V342_V244_DERIVE kind=nonzero")
            self.assertTrue(prior.is_file(),"V342_V244_DERIVE kind=no_output")
            try:
                completed=subprocess.run(
                    [sys.executable,str(V289),str(prior),str(staged)],
                    capture_output=True,text=True,timeout=180,
                    check=False,
                )
            except subprocess.TimeoutExpired:
                self.fail("V342_V289_DERIVE kind=timeout")
            self.assertEqual(completed.returncode,0,
                             "V342_V289_DERIVE kind=nonzero")
            self.assertTrue(staged.exists(),"V342_V289_DERIVE kind=no_output")
            source=staged.read_text(encoding="utf-8")
            self.assertEqual(source.count("V289_NAND_ENTRY n="),1)
            self.assertEqual(source.count("V278_FCA4_ENTRY n="),1)
            self.assertIn("v250_candidate_mode",source)
            with_service=service(source)
            self.assertIn("V296_SERVICE_ENTRY kind=",with_service)
            # The real original-free derivation rewrites the old V77
            # conditional. Test the assertion-associated branch instead
            # of the obsolete exact three-space header.
            self.assertIn("old=0 label=1 scoped=0 guest=1 branch=1",
                          ack_mmio_seam(with_service))
            self.assertEqual(with_service.count(ACK_MMIO_OLD),0)
            self.assertIn("label=1 scoped=0 guest=1 branch=1",
                          submit_mmio_seam(with_service))
            scoped=scope(with_service)
            self.assertIn("label=1 scoped=1 guest=1 branch=1",
                          submit_mmio_seam(scoped))
            self.assertEqual(scoped.count(ACK_MMIO_OLD),0)
            self.assertIn("old=0 label=1 scoped=1 guest=1 branch=1",
                          ack_mmio_seam(scoped))
            routed=mailbox_route(scoped)
            self.assertEqual(routed.count("V352_NAND_BUS kind="),2)
            self.assertIn("ipc70_bus.write32(addr,value)",routed)
            observed=mmio(routed)
            self.assertIn("V340_NAND_MMIO n=",observed)
            instrumented=entry(observed)
            self.assertIn("V321_GUEST_ENTRY pc=",instrumented)
            self.assertEqual(instrumented.count("V340_NAND_MMIO n="),1)
            self.assertEqual(instrumented.count("V352_NAND_BUS kind="),2)
            self.assertEqual(instrumented.count("V321_GUEST_ENTRY pc="),1)
            # Source-only instrumentation must not replace the original
            # hardware service calls with a fabricated IOS reply.
            self.assertIn("ipc70_bus.write32",instrumented)
            # The public-only V298 job has no NWiiRuntime checkout;
            # V351 source-only CI supplies the SHA-pinned patched runtime.
            # No CI result may call a skipped syntax check "verified".
            runtime_root=os.environ.get("V347_NWII_ROOT")
            if runtime_root is None:
                print("V351_PUBLIC_CPP source=1 syntax=0 runtime=0")
            else:
                self.assertTrue(
                    (Path(runtime_root)/"nWiiRuntime"/"include"/"runtime"/"cpu_context.h").is_file(),
                    "V351_PUBLIC_CPP runtime_headers_missing"
                )

                # V347: compile the complete independently derived PUBLIC harness
                # before any owner original/ELF step. Syntax-only means no native
                # game code is linked, loaded, or executed in this test.
                compiler=shutil.which("g++")
                self.assertIsNotNone(compiler,"V347_PUBLIC_CPP compiler_unavailable")
                staged_cpp=Path(td)/"v347-public-harness.cpp"
                staged_cpp.write_text(instrumented,encoding="utf-8")
                command=[
                    compiler,"-std=c++20","-fsyntax-only",
                    "-Wall","-Wextra","-Werror","-Wno-type-limits",
                    "-Wno-unused-label",
                    "-I"+str(HERE),
                    "-I"+str(Path(runtime_root)/"nWiiRuntime"/"include"),
                    str(staged_cpp),
                ]
                try:
                    result=subprocess.run(command,capture_output=True,text=True,
                                          timeout=120,check=False)
                except subprocess.TimeoutExpired:
                    self.fail("V347_PUBLIC_CPP compile_timeout")
                # V350: output only a compiler category and source-only line,
                # not raw C++ diagnostics or proprietary data.
                if result.returncode:
                    import re
                    errors=[line for line in result.stderr.splitlines()
                            if "error:" in line or "fatal error:" in line]
                    first=errors[0] if errors else ""
                    categories=(
                        ("undeclared", "undeclared"),
                        ("not declared", "undeclared"),
                        ("no member", "member"),
                        ("expected", "syntax"),
                        ("redefinition", "redefinition"),
                        ("ambiguous", "ambiguous"),
                        ("unused", "unused"),
                        ("does not name", "type"),
                        ("no matching function", "signature"),
                        ("invalid conversion", "conversion"),
                        ("fatal error:", "include"),
                    )
                    kind=next((name for token,name in categories if token in first),
                              "other")
                    match=re.search(r"v347-public-harness\.cpp:(\d+)",first)
                    line=int(match.group(1)) if match else 0
                    print(f"V350_PUBLIC_CPP_DIAG kind={kind} "
                          f"first_line={min(line,9999999)} "
                          f"errors={min(len(errors),9999)}",
                          flush=True)
                self.assertEqual(result.returncode,0,
                                 "V347_PUBLIC_CPP compile_failed")
                print("V347_PUBLIC_CPP source=1 syntax=1 original_free=1")
            print("V342_HARNESS_SMOKE scope=1 probe=1 entry=1 origfree=1")

if __name__=="__main__":
    unittest.main()
