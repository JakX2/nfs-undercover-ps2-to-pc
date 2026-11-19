#!/usr/bin/env python3
"""V113 source-only queue and native observer regression tests."""
from pathlib import Path
import tempfile,subprocess,unittest
from derive_v112_sc_async_submit_harness import derive as previous
from derive_v113_sc_transport_queue_harness import EDITS,derive
from derive_v113_sc_transport_queue_runner import derive as runner
HERE=Path(__file__).resolve().parent
class V113(unittest.TestCase):
 def test_harness(self):
  base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text()
  old=previous(base);s=derive(base);current=old
  for a,n in EDITS:
   self.assertEqual(current.count(a),1,a[:100]);current=current.replace(a,n,1)
  self.assertEqual(s,current)
  self.assertEqual(s,derive(base))
  self.assertIn("if(addr==0x805195ecu&&ctx.lr==0x80519924u)",s)
  self.assertNotIn("if(addr==POST_OWNER&&ctx.lr==0x80519924u)",s)
  self.assertEqual(s.count("V113_QUEUE_ENTRY"),1)
  self.assertEqual(s.count("POST_OWNER=0x805293b0u"),1)
  for marker in ("ctx.mmu.write","seed_stm_data(","ipc70_bus.reset()"):
   self.assertEqual(s.count(marker),old.count(marker))
 def test_runner(self):
  s=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
  for m in ("BOOT_PROGRESS entry=0x8000403C pc=0x805293B0 stage=113",
            "V113_QUEUE_ENTRY route=1 queue=1 abi=1 prior=1"):
   self.assertIn(m,s)
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"run.sh";p.write_text(s)
   subprocess.run(["bash","-n",str(p)],check=True)
if __name__=="__main__":unittest.main()
