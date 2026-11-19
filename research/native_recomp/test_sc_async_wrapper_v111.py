#!/usr/bin/env python3
"""V111 original-free overlay and source/runner contract checks."""
from pathlib import Path
import subprocess,tempfile,unittest
from derive_v110_sc_strlen_harness import derive as previous
from derive_v111_sc_async_wrapper_harness import EDITS,derive
from derive_v111_sc_async_wrapper_runner import derive as runner
HERE=Path(__file__).resolve().parent
class V111(unittest.TestCase):
 def test_harness(self):
  base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text()
  old=previous(base);s=derive(base)
  for a,_ in EDITS:self.assertEqual(old.count(a),1,a[:100])
  self.assertEqual(s,derive(base))
  for k in ("V111_SC_ASYNC_ENTRY","V111_TRIAL_PASS","POST_OWNER=0x8051982cu"):
   self.assertEqual(s.count(k),1)
  for k in ("ctx.mmu.write","seed_stm_data(","ipc70_bus.reset()"):
   self.assertEqual(s.count(k),old.count(k))
  self.assertIn("post111_copy_expected[i]=ctx.mmu.read8(s+i)",s)
 def test_runner(self):
  s=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
  self.assertIn("V111_STAGE native_test_passed",s)
  self.assertIn("V111_SC_ASYNC_ENTRY route=1 copied=1 path=1 nonempty=1 abi=1 prior=1",s)
  self.assertIn("BOOT_PROGRESS entry=0x8000403C pc=0x8051982C stage=111",s)
  self.assertIn('test "$branch" = 2',s)
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"run.sh";p.write_text(s)
   subprocess.run(["bash","-n",str(p)],check=True)
 def test_workflow(self):
  y=(HERE.parents[1]/".github/workflows/wii-v111-sc-async-wrapper.yml").read_text()
  self.assertIn("run_v111_continuous_sc_async_wrapper.sh",y)
  self.assertIn("stage=111",y)
  self.assertEqual(y.count("- name: Remove private owner and generated code"),1)
if __name__=="__main__":unittest.main()
