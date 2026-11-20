#!/usr/bin/env python3
"""Source-only V148 authentic repeated SC IPC read / next-leaf safety gates."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v147_sc_ipc_next_harness import derive as previous
from derive_v148_sc_ipc_distinct_harness import (
    derive, STATE, RESET, V147_STOP, V148_CONTINUE,
    V148_OBSERVER, V146_OBSERVER, NEXT_TRIAL,
)
from derive_v148_sc_ipc_distinct_runner import derive as runner, PASS

HERE=Path(__file__).resolve().parent

class V148(unittest.TestCase):
    def setUp(self):
        self.base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")

    def test_bounded_real_read_helper_and_new_handler_target(self):
        old=previous(self.base)
        new=derive(self.base)
        for token in (STATE,RESET,V147_STOP,V146_OBSERVER):
            self.assertEqual(old.count(token),1,token[:60])
        self.assertNotIn(V147_STOP,new)
        self.assertIn(V148_CONTINUE,new)
        self.assertIn(V148_OBSERVER,new)
        self.assertIn(NEXT_TRIAL,new)
        self.assertIn("if(v148_more_reads>32u)",new)
        self.assertIn("if(addr==0x8051905cu)",V148_OBSERVER)
        self.assertEqual(new.count("V148_SC_IPC_READ_LIMIT count="),1)
        self.assertEqual(new.count("V148_SC_IPC_DISTINCT first="),1)
        self.assertIn("ctx.inst_count>v148_start_inst",V148_OBSERVER)
        self.assertIn("ipc70_bus.services().queued_replies()==1u",V148_OBSERVER)
        self.assertIn("v148_distinct_seen==1u&&!c.is_running",new)

    def test_original_memory_and_cpu_state_unchanged(self):
        old=previous(self.base)
        new=derive(self.base)
        for t in ("ctx.mmu.write8(", "ctx.mmu.write16(", "ctx.mmu.write32(",
                  "ipc70_ram.write8(", "ipc70_bus.tick(",
                  "v139_scheduler.service_one(", "ipc70_bus.reset("):
            self.assertEqual(old.count(t),new.count(t),t)
        for pattern in (r"ctx\.gpr\[[^\]]+\]\s*=(?!=)",
                        r"ctx\.cr\[0\]\.eq\s*=(?!=)",
                        r"ctx\.msr\s*=(?!=)"):
            self.assertEqual(len(re.findall(pattern,old)),
                             len(re.findall(pattern,new)),pattern)

    def test_private_runner_and_precise_liveness_guards(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for token in ("derive_v148_sc_ipc_distinct_harness.py",
                      "V146_SC_IPC_LEAF verified=1",
                      "V147_SC_IPC_NEXT verified=1",
                      "V148_SC_IPC_DISTINCT verified=1",
                      "V148_SC_IPC_READ_LIMIT",
                      'test "$(grep -Ec'):
            self.assertIn(token,script)
        self.assertTrue(re.fullmatch(PASS,
            "V148_SC_IPC_DISTINCT first=1 caller=1 advanced=1 masked=1 queued=1 irq=1 reads=2 target=8051906c lr=80519394"))
        self.assertFalse(re.fullmatch(PASS,
            "V148_SC_IPC_DISTINCT first=0 caller=1 advanced=1 masked=1 queued=1 irq=1 reads=2 target=8051906c lr=80519394"))
        with tempfile.TemporaryDirectory() as td:
            file=Path(td)/"runner.sh";file.write_text(script)
            subprocess.run(["bash","-n",str(file)],check=True)

    def test_fail_closed_and_workflow_cleanup(self):
        with self.assertRaises(ValueError):derive("invalid")
        with self.assertRaises(ValueError):runner("invalid")
        wf=(HERE.parents[1]/".github/workflows/wii-v148-sc-ipc-distinct.yml").read_text()
        self.assertIn("run_v148_sc_ipc_distinct.sh",wf)
        self.assertIn("V148_SC_IPC_DISTINCT verified=1",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)

if __name__=="__main__":
    unittest.main()
