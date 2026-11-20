#!/usr/bin/env python3
"""Original-free V133 observable guest-byte state tests."""
import unittest,subprocess,tempfile
from pathlib import Path
from derive_v131_retry_state_harness import derive as previous
from derive_v133_sc_sda_harness import derive,OLD,NEW
from derive_v133_sc_sda_runner import derive as runner
HERE=Path(__file__).resolve().parent
class V133(unittest.TestCase):
    def test_read_only(self):
        src=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text()
        old=previous(src);self.assertEqual(old.count(OLD),1)
        now=derive(src);self.assertEqual(now,old.replace(OLD,NEW,1))
        self.assertIn("ctx.gpr[13]-3176u",now)
        self.assertIn("ctx.mmu.read8(v133_sda)",now)
        self.assertIn("V133_STATUS_BYTE mapped=",now)
        for k in ("ctx.mmu.write8(","ctx.mmu.write32(","ipc70_bus.reset()"):
            self.assertEqual(now.count(k),old.count(k))
    def test_runner_and_guards(self):
        text=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        self.assertIn('derive_v133_sc_sda_harness.py',text)
        self.assertIn('V133_STATUS_PROBE verified=1',text)
        self.assertIn('V131_STATE_PROBE verified=1',text)
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/"run.sh";f.write_text(text)
            subprocess.run(["bash","-n",str(f)],check=True)
    def test_workflow(self):
        w=(HERE.parents[1]/".github/workflows/wii-v133-sc-sda-state.yml").read_text()
        self.assertIn("V133_STATUS_PROBE verified=1",w)
        self.assertEqual(w.count("      - name: Remove private owner and generated code"),1)
if __name__=="__main__":unittest.main()
