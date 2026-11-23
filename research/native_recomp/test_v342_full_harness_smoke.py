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
import sys
import tempfile
import unittest

from derive_v296_service_harness import patch as service
from derive_v298_scope_reply_observer import (
    patch as scope, ack_mmio_seam, ACK_MMIO_OLD, ACK_MMIO_NEW,
)
from derive_v340_nand_mmio_probe import patch as mmio
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
            scoped=scope(with_service)
            self.assertEqual(scoped.count(ACK_MMIO_OLD),0)
            self.assertIn("old=0 label=1 scoped=1 guest=1 branch=1",
                          ack_mmio_seam(scoped))
            observed=mmio(scoped)
            self.assertIn("V340_NAND_MMIO n=",observed)
            instrumented=entry(observed)
            self.assertIn("V321_GUEST_ENTRY pc=",instrumented)
            self.assertEqual(instrumented.count("V340_NAND_MMIO n="),1)
            self.assertEqual(instrumented.count("V321_GUEST_ENTRY pc="),1)
            # Source-only instrumentation must not replace the original
            # hardware service calls with a fabricated IOS reply.
            self.assertIn("ipc70_bus.write32",instrumented)
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
                "-I"+str(HERE.parents[1]/"nWiiRuntime"/"include"),
                str(staged_cpp),
            ]
            try:
                result=subprocess.run(command,capture_output=True,text=True,
                                      timeout=120,check=False)
            except subprocess.TimeoutExpired:
                self.fail("V347_PUBLIC_CPP compile_timeout")
            # Keep compiler diagnostics/derived code in the transient
            # source-only CI scratch; report a stable status, not raw text.
            self.assertEqual(result.returncode,0,
                             "V347_PUBLIC_CPP compile_failed")
            print("V347_PUBLIC_CPP source=1 syntax=1 original_free=1")
            print("V342_HARNESS_SMOKE scope=1 probe=1 entry=1 origfree=1")

if __name__=="__main__":
    unittest.main()
