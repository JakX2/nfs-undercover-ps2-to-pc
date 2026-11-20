#!/usr/bin/env python3
"""Original-free V142 dispatcher continuation and fail-closed runner tests."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v141_sc_vector_harness import derive as previous
from derive_v142_sc_dispatch_harness import derive,STATE,RESET,HANDLER,TRIAL,NEXT,TRIAL_NEXT
from derive_v142_sc_dispatch_runner import derive as runner

HERE=Path(__file__).resolve().parent

class V142(unittest.TestCase):
    def test_only_releases_original_handler_and_adds_dispatch_observer(self):
        src=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text()
        old=previous(src)
        for anchor in (STATE,RESET,HANDLER,TRIAL):
            self.assertEqual(old.count(anchor),1,anchor[:75])
        now=derive(src)
        self.assertIn(NEXT,now)
        self.assertIn(TRIAL_NEXT,now)
        self.assertIn("v142_dispatch_seen==1u",now)
        self.assertIn("ctx.mmu.read32(frame+408u)==v141_resume",now)
        self.assertIn("ctx.mmu.read32(frame+4u*i)==v141_gprs[i]",now)
        self.assertEqual(now.count("V142_SC_DISPATCH route="),1)
        for s in ("ctx.mmu.write32(", "ctx.mmu.write8(", "ipc70_ram.write8("):
            self.assertEqual(now.count(s),old.count(s))
        for p in (r"ctx\.gpr\[3\]\s*=(?!=)",r"ctx\.cr\[0\]\.eq\s*=(?!=)"):
            self.assertEqual(len(re.findall(p,now)),len(re.findall(p,old)))

    def test_runner_and_shell_syntax(self):
        s=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for t in ("derive_v142_sc_dispatch_harness.py",
                  "V140_SC_IRQ_ENTRY verified=1",
                  "V141_SC_VECTOR verified=1",
                  "V142_SC_DISPATCH verified=1"):
            self.assertIn(t,s)
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"native.sh"
            path.write_text(s)
            subprocess.run(["bash","-n",str(path)],check=True)

    def test_missing_anchors_fail_closed(self):
        with self.assertRaises(ValueError):derive("unrelated")
        with self.assertRaises(ValueError):runner("unrelated")

    def test_private_workflow_safely_cleans_owner(self):
        s=(HERE.parents[1]/".github/workflows/wii-v142-sc-dispatch.yml").read_text()
        self.assertIn("run_v142_sc_dispatch.sh",s)
        self.assertIn("V142_SC_DISPATCH verified=1",s)
        self.assertEqual(s.count("      - name: Remove private owner and generated code"),1)

if __name__=="__main__":
    unittest.main()
