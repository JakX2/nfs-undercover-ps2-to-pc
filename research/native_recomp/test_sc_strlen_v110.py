#!/usr/bin/env python3
"""V110 original-free overlay, native runner and workflow guards."""
from pathlib import Path
import subprocess
import tempfile
import unittest
from derive_v109_sc_nonempty_harness import derive as previous
from derive_v110_sc_strlen_harness import derive,EDITS
from derive_v110_sc_strlen_runner import derive as runner
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
class V110(unittest.TestCase):
    def test_harness(self):
        base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text()
        prior=previous(base)
        result=derive(base)
        for old,_ in EDITS:self.assertEqual(prior.count(old),1,old[:80])
        for marker in ("V110_SC_STRLEN","V110_SC_CONTINUE","V110_TRIAL_PASS","POST_OWNER=0x8051e518u"):
            self.assertEqual(result.count(marker),1)
        self.assertEqual(result.count("ctx.mmu.write"),prior.count("ctx.mmu.write"))
        self.assertEqual(result.count("seed_stm_data("),prior.count("seed_stm_data("))
        self.assertEqual(result.count("ipc70_bus.reset()"),prior.count("ipc70_bus.reset()"))
        self.assertEqual(result,derive(base))
    def test_runner(self):
        s=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for marker in ("derive_v110_sc_strlen_harness.py","V110_NATIVE_EXIT ok=1",
                       "V110_NATIVE_EXIT ok=0","V110_SC_CONTINUE route=1 data=1 abi=1 prior=1 branch=[123]",
                       "BOOT_PROGRESS entry=0x8000403C pc=$target stage=110"):
            self.assertIn(marker,s)
        self.assertLess(s.index("V104_STAGE native_compiled"),s.index("V110_NATIVE_EXIT ok=1"))
        self.assertNotIn("V104_SUCCESS_GATE",s)
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/"run.sh";f.write_text(s)
            subprocess.run(["bash","-n",str(f)],check=True)
    def test_workflow(self):
        y=(ROOT/".github/workflows/wii-v110-sc-strlen.yml").read_text()
        self.assertIn("run_v110_continuous_sc_strlen.sh",y)
        self.assertIn("V110_STAGE native_test_passed",y)
        self.assertIn("pc=0x(8051E518|804F1E2C|8051E3DC) stage=110",y)
        self.assertNotIn("grep -Fx 'V107_SC_SOURCE",y)
if __name__=="__main__":unittest.main()
