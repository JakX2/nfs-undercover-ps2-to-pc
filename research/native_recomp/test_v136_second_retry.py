#!/usr/bin/env python3
"""V136 original-free unit checks for bounded second authentic SC retry."""
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v133_sc_sda_harness import derive as previous
from derive_v136_second_retry_harness import (
    derive, STATE_ANCHOR, RESET_ANCHOR, STOP_ANCHOR, STOP_REPLACEMENT
)
from derive_v136_second_retry_runner import derive as derive_runner

HERE = Path(__file__).resolve().parent


class V136(unittest.TestCase):
    def test_previous_harness_and_exact_stop_replacement(self):
        source = (HERE / "test_start_to_ipc_ack_v77.cpp").read_text()
        old = previous(source)
        self.assertEqual(old.count(STATE_ANCHOR), 1)
        self.assertEqual(old.count(RESET_ANCHOR), 1)
        self.assertEqual(old.count(STOP_ANCHOR), 1)
        actual = derive(source)
        self.assertEqual(actual.count(STOP_REPLACEMENT), 1)
        self.assertNotIn(STOP_ANCHOR, actual)
        self.assertEqual(actual.count("V136_SECOND_PASS pc="), 1)
        self.assertEqual(actual.count("post136_disable=0,post136_restore=0,post136_seen=0;"), 1)
        self.assertIn("post136_seen=0;", actual)
        self.assertIn("post130_next==1u&&addr==0x8052f830u", actual)
        self.assertIn("check(mapped&&status==1u&&ctx.gpr[3]==1u", actual)

    def test_never_mutates_sc_state(self):
        source = (HERE / "test_start_to_ipc_ack_v77.cpp").read_text()
        before = previous(source)
        after = derive(source)
        for term in ("ctx.mmu.write8(", "ctx.mmu.write16(",
                     "ctx.mmu.write32(", "ipc70_bus.reset()"):
            self.assertEqual(before.count(term), after.count(term))
        self.assertIn("++post136_disable;", after)
        self.assertIn("++post136_restore;", after)
        self.assertIn("post136_disable==1u&&post136_restore==1u", after)

    def test_runner_is_syntactically_valid_and_preserves_old_gates(self):
        source = (HERE / "run_v79_continuous_reply_entry.sh").read_text()
        runner = derive_runner(source)
        for term in ('derive_v136_second_retry_harness.py',
                     "V131_STATE_PROBE verified=1",
                     "V133_STATUS_PROBE verified=1",
                     "V136_SECOND_RETRY verified=1",
                     "V130_STAGE native_test_passed",
                     "BOOT_PROGRESS entry=0x8000403C"):
            self.assertIn(term, runner)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "run.sh"
            path.write_text(runner)
            subprocess.run(["bash", "-n", str(path)], check=True)

    def test_rejects_missing_inherited_anchor(self):
        with self.assertRaises(ValueError):
            derive_runner("broken")
        with self.assertRaises(ValueError):
            derive("broken")


if __name__ == "__main__":
    unittest.main()
