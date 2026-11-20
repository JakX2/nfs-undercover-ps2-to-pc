#!/usr/bin/env python3
"""Original-free V140 Wii external IRQ entry and regression-gate tests."""
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v139_sc_ios_service_harness import derive as previous
from derive_v140_sc_irq_entry_harness import derive,STOP,NEW
from derive_v140_sc_irq_entry_runner import derive as derive_runner
HERE=Path(__file__).resolve().parent

class V140(unittest.TestCase):
    def test_only_changes_original_free_terminal_observer(self):
        source=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text()
        old=previous(source)
        self.assertEqual(old.count(STOP),1)
        derived=derive(source)
        self.assertEqual(derived,old.replace(STOP,NEW,1))
        self.assertEqual(derived.count("V140_SC_IRQ_ENTRY pending="),1)
        self.assertIn("enter_external_irq(",derived)
        self.assertIn("irq74_vector,true",derived)
        self.assertIn("post90_target=addr;observed_stop_pc=v140_resume;",derived)
        for op in ("ctx.mmu.write8(", "ctx.mmu.write32(",
                   "ipc70_ram.write8(", "ctx.gpr[3]=", "ctx.cr[0].eq="):
            self.assertEqual(old.count(op),derived.count(op))

    def test_fail_closed_native_wrapper(self):
        s=derive_runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for token in ("derive_v140_sc_irq_entry_harness.py",
                      "V138_REQUEST_PROBE verified=1",
                      "V139_SC_ACK verified=1",
                      "V140_SC_IRQ_ENTRY verified=1",
                      "BOOT_PROGRESS entry=0x8000403C"):
            self.assertIn(token,s)
        with tempfile.TemporaryDirectory() as td:
            script=Path(td)/"run.sh"
            script.write_text(s)
            subprocess.run(["bash","-n",str(script)],check=True)

    def test_anchor_safety(self):
        with self.assertRaises(ValueError):derive("bad")
        with self.assertRaises(ValueError):derive_runner("bad")

if __name__=="__main__":
    unittest.main()
