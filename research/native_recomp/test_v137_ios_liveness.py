#!/usr/bin/env python3
"""V137 source-only native IPC liveness observer regression."""
from pathlib import Path
import tempfile,subprocess,unittest
from derive_v136_second_retry_harness import derive as previous
from derive_v137_ios_liveness_harness import derive,OLD,NEW
from derive_v137_ios_liveness_runner import derive as runner
HERE=Path(__file__).resolve().parent
class V137(unittest.TestCase):
    def test_original_memory_and_ios_untouched(self):
        source=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text()
        old=previous(source);actual=derive(source)
        self.assertEqual(old.count(OLD),1)
        self.assertEqual(actual,old.replace(OLD,NEW,1))
        for marker in ("V137_IOS_LIVENESS x1=","queued_replies()",
                       "event_pending()","external_irq_level()","V136_SECOND_PASS pc="):
            self.assertIn(marker,actual)
        for marker in ("ipc70_bus.tick(","ctx.mmu.write8(","ctx.mmu.write32(","ipc70_bus.reset()"):
            self.assertEqual(actual.count(marker),old.count(marker))
    def test_runner(self):
        s=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for marker in ("derive_v137_ios_liveness_harness.py","V137_IOS_PROBE verified=1",
                       "V136_SECOND_RETRY verified=1","V133_STATUS_PROBE verified=1"):
            self.assertIn(marker,s)
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"run.sh";p.write_text(s)
            subprocess.run(["bash","-n",str(p)],check=True)
    def test_owner_ci(self):
        wf=(HERE.parents[1]/".github/workflows/wii-v137-ios-liveness.yml").read_text()
        self.assertIn("V137_IOS_PROBE verified=1",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
if __name__=="__main__":unittest.main()
