#!/usr/bin/env python3
"""Original-free V144 timebase return into native IRQ scheduler-disable tests."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v143_sc_irq_time_harness import derive as previous
from derive_v144_sc_irq_disable_harness import derive,STATE,RESET,STOP,TRIAL,NEXT,NEXT_TRIAL
from derive_v144_sc_irq_disable_runner import derive as runner

HERE=Path(__file__).resolve().parent

class V144(unittest.TestCase):
    def test_canonical_guest_body_and_memory_preserved(self):
        source=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text()
        old=previous(source)
        for anchor in (STATE,RESET,STOP,TRIAL):
            self.assertEqual(old.count(anchor),1,anchor[:75])
        result=derive(source)
        self.assertIn(NEXT,result)
        self.assertIn(NEXT_TRIAL,result)
        self.assertIn("ctx.lr==0x80526c98u",result)
        self.assertIn("ctx.inst_count>v144_time_inst",result)
        self.assertEqual(result.count("V144_SC_DISABLE route="),1)
        for term in ("ctx.mmu.write8(", "ctx.mmu.write32(", "ipc70_ram.write8("):
            self.assertEqual(result.count(term),old.count(term))
        for pattern in (r"ctx\.gpr\[3\]\s*=(?!=)",r"ctx\.cr\[0\]\.eq\s*=(?!=)"):
            self.assertEqual(len(re.findall(pattern,result)),len(re.findall(pattern,old)))

    def test_runner_keeps_prior_gates(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for marker in ("derive_v144_sc_irq_disable_harness.py",
                       "V142_SC_DISPATCH verified=1",
                       "V143_SC_TIME verified=1",
                       "V144_SC_DISABLE verified=1"):
            self.assertIn(marker,script)
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"run.sh";path.write_text(script)
            subprocess.run(["bash","-n",str(path)],check=True)

    def test_failure_and_private_cleanup(self):
        with self.assertRaises(ValueError):derive("missing")
        with self.assertRaises(ValueError):runner("missing")
        wf=(HERE.parents[1]/".github/workflows/wii-v144-sc-disable.yml").read_text()
        self.assertIn("run_v144_sc_irq_disable.sh",wf)
        self.assertIn("V144_SC_DISABLE verified=1",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)

if __name__=="__main__":
    unittest.main()
