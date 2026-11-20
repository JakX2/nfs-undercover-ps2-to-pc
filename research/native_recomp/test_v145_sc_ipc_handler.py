#!/usr/bin/env python3
"""V145 source-only authentic SC IPC handler continuation guards."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v144_sc_irq_disable_harness import derive as previous
from derive_v145_sc_ipc_handler_harness import derive,STATE,RESET,STOP,TRIAL,NEXT,NEXT_TRIAL
from derive_v145_sc_ipc_handler_runner import derive as runner
HERE=Path(__file__).resolve().parent

class V145(unittest.TestCase):
    def test_provenance_and_guest_state_are_unchanged(self):
        original=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text()
        prior=previous(original)
        for anchor in (STATE,RESET,STOP,TRIAL):
            self.assertEqual(prior.count(anchor),1,anchor[:75])
        now=derive(original)
        self.assertIn(NEXT,now)
        self.assertIn(NEXT_TRIAL,now)
        # The V136 retry observer must not capture IRQ helper calls
        # after the third SC status entry. Its assertions still run
        # unaltered during the actual second SC retry.
        for addr in ("0x805265acu","0x805265d4u"):
            before=f"if(post130_next==1u&&addr=={addr})"
            after=f"if(post130_next==1u&&post136_seen==0u&&addr=={addr})"
            self.assertEqual(prior.count(before),1)
            self.assertEqual(now.count(before),0)
            self.assertEqual(now.count(after),1)
        self.assertIn("V136 second original SC critical section out of order",now)
        self.assertIn("V136 second original SC restore mismatch",now)
        for marker in ("ctx.ctr==addr","ctx.gpr[3]==27u",
                       "ctx.mmu.read32(IRQ_TABLE+27u*4u)==addr",
                       "ctx.inst_count>v145_disable_inst"):
            self.assertIn(marker,now)
        self.assertEqual(now.count("V145_SC_IPC dispatch="),1)
        for term in ("ctx.mmu.write8(", "ctx.mmu.write32(", "ipc70_ram.write8("):
            self.assertEqual(now.count(term),prior.count(term))
        for pattern in (r"ctx\.gpr\[3\]\s*=(?!=)",r"ctx\.cr\[0\]\.eq\s*=(?!=)"):
            self.assertEqual(len(re.findall(pattern,now)),len(re.findall(pattern,prior)))

    def test_inherited_runner_and_native_cleanup(self):
        s=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for marker in ("derive_v145_sc_ipc_handler_harness.py",
                       "V143_SC_TIME verified=1",
                       "V144_SC_DISABLE verified=1",
                       "V145_SC_IPC verified=1"):
            self.assertIn(marker,s)
        with tempfile.TemporaryDirectory() as td:
            script=Path(td)/"run.sh";script.write_text(s)
            subprocess.run(["bash","-n",str(script)],check=True)
        wf=(HERE.parents[1]/".github/workflows/wii-v145-sc-ipc.yml").read_text()
        self.assertIn("run_v145_sc_ipc_handler.sh",wf)
        self.assertIn("V145_SC_IPC verified=1",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)

    def test_missing_source_fails_closed(self):
        with self.assertRaises(ValueError):derive("invalid")
        with self.assertRaises(ValueError):runner("invalid")

if __name__=="__main__":
    unittest.main()
