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
   count=2 if a=="if(addr==POST_OWNER&&ctx.lr==0x80519924u){" else 1
   self.assertEqual(current.count(a),count,a[:100]);current=current.replace(a,n,count)
  self.assertEqual(s,current)
  self.assertEqual(s,derive(base))
  self.assertEqual(s.count("if(addr==0x805195ecu&&ctx.lr==0x80519924u)"),2)
  self.assertNotIn("if(addr==POST_OWNER&&ctx.lr==0x80519924u)",s)
  self.assertEqual(s.count("V113_QUEUE_ENTRY"),1)
  self.assertEqual(s.count("POST_OWNER=0x805293b0u"),1)
  for marker in ("ctx.mmu.write","seed_stm_data(","ipc70_bus.reset()"):
   self.assertEqual(s.count(marker),old.count(marker))
 def test_workflow_paths_and_provenance(self):
  workflow=(HERE.parents[1]/".github/workflows/wii-v113-sc-transport-queue.yml").read_text()
  for source in ("run_v113_continuous_sc_transport_queue.sh",
                 "diagnose_sc_transport_queue_v113.py"):
   self.assertTrue((HERE/source).is_file(),source)
   self.assertIn(source,workflow)
  self.assertNotIn("run_v113_continuous_sc_async_submit.sh",workflow)
  self.assertNotIn("diagnose_sc_async_submit_v113.py",workflow)
  self.assertIn("'.github/workflows/wii-v113-sc-transport-queue.yml'",workflow)
  self.assertIn("^V112_ASYNC_SUBMIT",workflow)
  self.assertIn("^V112_ASYNC_SYSCALL",workflow)
  self.assertIn("V113_QUEUE_ENTRY route=1 queue=1 abi=1 prior=1",workflow)
 def test_runner(self):
  s=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
  for m in ("BOOT_PROGRESS entry=0x8000403C pc=0x805293B0 stage=113",
            "V113_QUEUE_ENTRY route=1 queue=1 abi=1 prior=1"):
   self.assertIn(m,s)
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"run.sh";p.write_text(s)
   subprocess.run(["bash","-n",str(p)],check=True)
if __name__=="__main__":unittest.main()
