#!/usr/bin/env python3
"""V90 original-free dynamic route checkpoint and runner regression."""
import unittest
import subprocess
import tempfile
from pathlib import Path
from derive_v89_post_stm_harness import derive as previous
from derive_v90_console_route_harness import EDITS, derive
from derive_v90_console_route_runner import derive as runner
HERE=Path(__file__).resolve().parent
class ConsoleRouteTest(unittest.TestCase):
    def test_harness(self):
        base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text()
        prior=previous(base);s=derive(base)
        for a,_ in EDITS:
            self.assertEqual(prior.count(a),1)
        self.assertEqual(s,derive(base))
        for marker in ("V90_CONSOLE_ROUTE","V90_ROUTE_TARGET","V90_TRIAL_PASS","POST_OWNER=0x8052f94cu"):
            self.assertEqual(s.count(marker),1)
        self.assertIn("ctx.lr==(first?0x8052f7f0u:0x8052f80cu)",s)
        self.assertIn("observed_stop_pc==(owner?nwii::runtime::post90_target:POST_SYNTH)",s)
        self.assertEqual(s.count("ctx.mmu.write"),prior.count("ctx.mmu.write"))
        self.assertEqual(s.count("ipc70_bus.reset()"),prior.count("ipc70_bus.reset()"))
    def test_runner(self):
        s=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        self.assertIn("stop=0x(8051e7e4|8052f94c)",s)
        self.assertIn("V90_ROUTE_TARGET",s)
        self.assertIn("for mode in 0 1 2 3",s)
        self.assertIn("restore_post_stm_v89.py",s)
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"run.sh";p.write_text(s)
            subprocess.run(["bash","-n",str(p)],check=True)
if __name__=="__main__":
    unittest.main()
