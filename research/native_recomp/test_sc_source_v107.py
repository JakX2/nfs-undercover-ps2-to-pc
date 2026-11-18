#!/usr/bin/env python3
"""Original-free V107 provenance observer/runner regression."""
import unittest
from pathlib import Path
from derive_v104_sc_async_submit_harness import derive as prior
from derive_v107_sc_source_probe_harness import derive
from derive_v107_sc_source_runner import derive as runner
ROOT=Path(__file__).resolve().parent
class SourceProbe(unittest.TestCase):
    def test_overlay_read_only(self):
        base=(ROOT/"test_start_to_ipc_ack_v77.cpp").read_text()
        before=prior(base);actual=derive(base)
        self.assertEqual(actual.count("V107_SC_SOURCE mapped="),1)
        self.assertEqual(actual.count('"/shared2/sys/SYSCONF"'),1)
        self.assertIn("{ // keep V107 probe locals separate from original caller declarations",actual)
        self.assertEqual(before.count("ctx.mmu.write"),actual.count("ctx.mmu.write"))
        self.assertEqual(before.count("seed_stm_data("),actual.count("seed_stm_data("))
        self.assertEqual(before.count("ipc70_bus.reset()"),actual.count("ipc70_bus.reset()"))
    def test_runner_is_diagnostic_only(self):
        base=(ROOT/"run_v79_continuous_reply_entry.sh").read_text()
        actual=runner(base)
        self.assertIn("derive_v107_sc_source_probe_harness.py",actual)
        self.assertIn("BOOT_PROGRESS entry=0x8000403C pc=0x805195EC stage=104",actual)
if __name__=="__main__":unittest.main()
