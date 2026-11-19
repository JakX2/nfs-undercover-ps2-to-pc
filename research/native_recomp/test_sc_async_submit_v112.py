#!/usr/bin/env python3
"""V112 original-free authenticated SC IOS_OpenAsync request checks."""
from pathlib import Path
import tempfile,subprocess,unittest
from derive_v111_sc_async_wrapper_harness import derive as previous
from derive_v112_sc_async_submit_harness import EDITS,derive
from derive_v112_sc_async_submit_runner import derive as runner
HERE=Path(__file__).resolve().parent
class V112(unittest.TestCase):
 def test_harness(self):
  base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text()
  old=previous(base);s=derive(base);current=old
  for a,n in EDITS:
   self.assertEqual(current.count(a),1,a[:100])
   current=current.replace(a,n,1)
  self.assertEqual(s,current)
  self.assertEqual(s,derive(base))
  self.assertIn("if(addr==0x8051982cu&&ctx.lr==0x804f1eccu)",s)
  self.assertNotIn("if(addr==POST_OWNER&&ctx.lr==0x804f1eccu)",s)
  for marker in ("V112_ASYNC_SYSCALL","V112_ASYNC_SUBMIT","V112_BOUNDARY","V112_TRIAL_PASS",
                 "POST_OWNER=0x805195ecu"):
   self.assertEqual(s.count(marker),1)
  for marker in ("ctx.mmu.write","seed_stm_data(","ipc70_bus.reset()"):
   self.assertEqual(s.count(marker),old.count(marker))
 def test_runner(self):
  s=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
  for m in ("V112_STAGE native_test_passed","BOOT_PROGRESS entry=0x8000403C pc=0x805195EC stage=112",
            "V112_ASYNC_SUBMIT route=1 wire=1 mode=1 path=1 abi=1 prior=1"):
   self.assertIn(m,s)
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"run.sh";p.write_text(s)
   subprocess.run(["bash","-n",str(p)],check=True)
 def test_workflow(self):
  y=(HERE.parents[1]/".github/workflows/wii-v112-sc-async-submit.yml").read_text()
  self.assertIn("run_v112_continuous_sc_async_submit.sh",y)
  self.assertIn("diagnose_sc_async_submit_v112.py",y)
  self.assertIn("pc=0x805195EC stage=112",y)
  self.assertEqual(y.count("- name: Remove private owner and generated code"),1)
if __name__=="__main__":unittest.main()
