#!/usr/bin/env python3
"""Original-free authenticated SC data restoration overlay regression."""
import unittest
from pathlib import Path
from derive_v107_sc_source_probe_harness import derive as prior
from derive_v108_sc_literal_restore_harness import derive
from derive_v108_sc_literal_runner import derive as runner
HERE=Path(__file__).resolve().parent
class Restore(unittest.TestCase):
    def test_overlay(self):
        base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text()
        before=prior(base);after=derive(base)
        self.assertEqual(after.count("V108_SC_RESTORE owner="),1)
        self.assertEqual(after.count("V107_SC_SOURCE mapped="),1)
        self.assertEqual(after.count("seed_stm_data(ctx,s,unsigned(public_sc.size()+1u))"),1)
        self.assertEqual(before.count("seed_stm_data(")+1,after.count("seed_stm_data("))
        self.assertEqual(before.count("ctx.mmu.write"),after.count("ctx.mmu.write"))
        self.assertEqual(before.count("ipc70_bus.reset()"),after.count("ipc70_bus.reset()"))
        self.assertIn("check(owner_match&&guest_empty&&open71_ram",after)
    def test_runner(self):
        s=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        self.assertIn("derive_v108_sc_literal_restore_harness.py",s)
        self.assertIn("BOOT_PROGRESS entry=0x8000403C pc=0x805195EC stage=104",s)
if __name__=="__main__":unittest.main()
