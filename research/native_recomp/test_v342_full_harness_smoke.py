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
V289=HERE/"derive_v289_nand_entry_r3_harness.py"

class Tests(unittest.TestCase):
    def test_full_original_free_source_derivation_chain(self):
        with tempfile.TemporaryDirectory(prefix="v342-public-") as td:
            staged=Path(td)/"v289.cpp"
            self.assertTrue(SOURCE.is_file() and V289.is_file())
            try:
                completed=subprocess.run(
                    [sys.executable,str(V289),str(SOURCE),str(staged)],
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
            self.assertIn("old=1 label=1 scoped=0 guest=1",
                          ack_mmio_seam(with_service))
            self.assertEqual(with_service.count(ACK_MMIO_OLD),1)
            scoped=scope(with_service)
            self.assertEqual(scoped.count(ACK_MMIO_OLD),0)
            self.assertEqual(scoped.count(ACK_MMIO_NEW),1)
            self.assertIn("old=0 label=1 scoped=1 guest=1",
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
            print("V342_HARNESS_SMOKE scope=1 probe=1 entry=1 origfree=1")

if __name__=="__main__":
    unittest.main()
