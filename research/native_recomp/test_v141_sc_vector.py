#!/usr/bin/env python3
"""Original-free V141 source/runner safety and exception-vector tests."""
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v140_sc_irq_entry_harness import derive as previous
from derive_v141_sc_vector_harness import (
    derive,STATE,RESET,INJECT,TRACE,TRIAL,BEFORE_STOP,ENTRY_OBSERVER,TRIAL_EXTRA
)
from derive_v141_sc_vector_runner import derive as runner

HERE=Path(__file__).resolve().parent

class V141(unittest.TestCase):
    def test_only_adds_test_owned_context_observers(self):
        src=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text()
        old=previous(src)
        for anchor in (STATE,RESET,INJECT,TRACE,TRIAL):
            self.assertEqual(old.count(anchor),1,anchor[:80])
        now=derive(src)
        self.assertIn(BEFORE_STOP,now)
        self.assertIn(ENTRY_OBSERVER,now)
        self.assertIn(TRIAL_EXTRA,now)
        self.assertIn("v141_vector_seen==1u",now)
        self.assertIn("ctx.mmu.read32(frame+412u)==v141_srr1",now)
        self.assertIn("run_game(c);",now)
        self.assertIn("ctx.is_running=false;throw ExceptionStop{}",now)
        for forbidden in ("ctx.mmu.write32(", "ctx.mmu.write8(",
                          "ipc70_ram.write8(", "ctx.gpr[3]=", "ctx.cr[0].eq="):
            self.assertEqual(now.count(forbidden),old.count(forbidden))
        self.assertEqual(now.count("V141_SC_VECTOR vector="),1)

    def test_fail_closed_native_runner(self):
        src=(HERE/"run_v79_continuous_reply_entry.sh").read_text()
        s=runner(src)
        for term in ("derive_v141_sc_vector_harness.py",
                     "V139_SC_ACK verified=1",
                     "V140_SC_IRQ_ENTRY verified=1",
                     "V141_SC_VECTOR verified=1",
                     "BOOT_PROGRESS entry=0x8000403C"):
            self.assertIn(term,s)
        with tempfile.TemporaryDirectory() as td:
            file=Path(td)/"derived.sh"
            file.write_text(s)
            subprocess.run(["bash","-n",str(file)],check=True)

    def test_rejects_missing_source_anchors(self):
        with self.assertRaises(ValueError):derive("unrelated")
        with self.assertRaises(ValueError):runner("unrelated")

    def test_private_workflow_preserves_cleanup(self):
        s=(HERE.parents[1]/".github/workflows/wii-v141-sc-vector.yml").read_text()
        self.assertIn("run_v141_sc_vector.sh",s)
        self.assertIn("V141_SC_VECTOR verified=1",s)
        self.assertIn("WII_ORIGINAL_DOL_ID",s)
        self.assertEqual(s.count("      - name: Remove private owner and generated code"),1)

if __name__=="__main__":
    unittest.main()
