#!/usr/bin/env python3
"""Source-only V143 original IRQ timebase entry and guest-state guards."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v142_sc_dispatch_harness import derive as previous
from derive_v143_sc_irq_time_harness import derive,STATE,RESET,STOP,TRIAL,REPLACE,NEXT_TRIAL
from derive_v143_sc_irq_time_runner import derive as runner

HERE=Path(__file__).resolve().parent

class V143(unittest.TestCase):
    def test_owner_guest_execution_remains_unchanged(self):
        source=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text()
        old=previous(source)
        for anchor in (STATE,RESET,STOP,TRIAL):self.assertEqual(old.count(anchor),1,anchor[:72])
        result=derive(source)
        self.assertIn(REPLACE,result)
        self.assertIn(NEXT_TRIAL,result)
        self.assertIn("ctx.inst_count>v143_dispatch_inst",result)
        self.assertIn("ctx.lr==0x80526c84u",result)
        self.assertEqual(result.count("V143_SC_TIME time="),1)
        for pattern in ("ctx.mmu.write8(", "ctx.mmu.write32(", "ipc70_ram.write8("):
            self.assertEqual(result.count(pattern),old.count(pattern))
        for pattern in (r"ctx\.gpr\[3\]\s*=(?!=)",r"ctx\.cr\[0\]\.eq\s*=(?!=)"):
            self.assertEqual(len(re.findall(pattern,result)),len(re.findall(pattern,old)))

    def test_runner_preserves_checkpoint_chain(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for marker in ("derive_v143_sc_irq_time_harness.py",
                       "V141_SC_VECTOR verified=1",
                       "V142_SC_DISPATCH verified=1",
                       "V143_SC_TIME verified=1",
                       "BOOT_PROGRESS entry=0x8000403C"):
            self.assertIn(marker,script)
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"run.sh";path.write_text(script)
            subprocess.run(["bash","-n",str(path)],check=True)

    def test_fail_closed(self):
        with self.assertRaises(ValueError):derive("invalid")
        with self.assertRaises(ValueError):runner("invalid")

    def test_private_ci_cleanup(self):
        wf=(HERE.parents[1]/".github/workflows/wii-v143-sc-time.yml").read_text()
        self.assertIn("run_v143_sc_irq_time.sh",wf)
        self.assertIn("V143_SC_TIME verified=1",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)

if __name__=="__main__":
    unittest.main()
