#!/usr/bin/env python3
"""V131 original-free retry register and condition code test."""
from pathlib import Path
import subprocess,tempfile,unittest
from derive_v130_irq_restore_harness import derive as previous
from derive_v131_retry_state_harness import derive,OLD,NEW
from derive_v131_retry_state_runner import derive as runner
HERE=Path(__file__).resolve().parent
class V131NativeProbe(unittest.TestCase):
    def test_harness_only_adds_guest_state_check(self):
        source=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text()
        old=previous(source)
        self.assertEqual(old.count(OLD),1)
        actual=derive(source)
        self.assertEqual(actual,old.replace(OLD,NEW,1))
        self.assertIn("V131_RETRY_STATE pc=",actual)
        self.assertIn("ctx.cr[0].eq",actual)
        self.assertIn("check(retry_back&&ctx.cr[0].eq",actual)
    def test_runner_uses_real_v130_execution(self):
        s=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for m in ('python3 "$here/derive_v131_retry_state_harness.py"',
                  "V130_STAGE native_test_passed","V131_STATE_PROBE verified=1",
                  "V131_RETRY_STATE pc=8052f830 lr=80520970",
                  "BOOT_PROGRESS entry=0x8000403C pc=0x${candidate^^} stage=130"):
            self.assertIn(m,s)
        with tempfile.TemporaryDirectory() as d:
            file=Path(d)/"run.sh";file.write_text(s)
            subprocess.run(["bash","-n",str(file)],check=True)
    def test_private_workflow(self):
        wf=(HERE.parents[1]/".github/workflows/wii-v131-retry-state.yml").read_text()
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        for m in ("run_v131_retry_state.sh","V131_STATE_PROBE verified=1",
                  "V130_NATIVE_EXIT ok=1",
                  "WII_ORIGINAL_DOL_ID","WII_ORIGINAL_ELF_ID"):
            self.assertIn(m,wf)
if __name__=="__main__":
    unittest.main()
