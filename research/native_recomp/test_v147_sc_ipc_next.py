#!/usr/bin/env python3
"""V147 original-free SC IPC first leaf return / caller successor regressions."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v146_sc_ipc_leaf_harness import derive as previous
from derive_v147_sc_ipc_next_harness import (
    derive, STATE, RESET, V146_STOP, V146_OBSERVER, V147_OBSERVER,
    V147_CONTINUE, NEXT_TRIAL,
)
from derive_v147_sc_ipc_next_runner import derive as runner, PASS

HERE=Path(__file__).resolve().parent

class V147(unittest.TestCase):
    def setUp(self):
        self.base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")

    def test_original_helper_is_allowed_to_execute(self):
        old=previous(self.base)
        now=derive(self.base)
        for anchor in (STATE,RESET,V146_STOP,V146_OBSERVER):
            self.assertEqual(old.count(anchor),1,anchor[:64])
        self.assertNotIn(V146_STOP,now)
        self.assertIn(V147_CONTINUE,now)
        self.assertIn(V147_OBSERVER,now)
        self.assertIn(NEXT_TRIAL,now)
        self.assertEqual(now.count("V147_SC_IPC_NEXT first="),1)
        self.assertIn("v147_first_target==0x8051905cu",now)
        self.assertIn("ctx.inst_count>v147_first_inst",now)
        self.assertIn("ctx.lr>=0x80519318u&&ctx.lr<0x805194c4u",now)
        self.assertIn("ipc70_bus.services().queued_replies()==1u",now)
        self.assertIn("ctx.is_running=false;throw ExceptionStop{};",V147_OBSERVER)

    def test_no_guest_mutation_or_new_ios_pumping(self):
        old=previous(self.base)
        new=derive(self.base)
        for expression in ("ctx.mmu.write8(", "ctx.mmu.write16(",
                           "ctx.mmu.write32(", "ipc70_ram.write8(",
                           "ipc70_bus.tick(", "v139_scheduler.service_one(",
                           "ipc70_bus.reset("):
            self.assertEqual(new.count(expression),old.count(expression),expression)
        for pattern in (r"ctx\.gpr\[[^\]]+\]\s*=(?!=)",
                        r"ctx\.cr\[0\]\.eq\s*=(?!=)",
                        r"ctx\.msr\s*=(?!=)"):
            self.assertEqual(len(re.findall(pattern,new)),
                             len(re.findall(pattern,old)),pattern)

    def test_runner_keeps_prior_gates_and_requires_sixteen(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        self.assertIn("derive_v147_sc_ipc_next_harness.py",script)
        for gate in ("V140_SC_IRQ_ENTRY verified=1",
                     "V145_SC_IPC verified=1",
                     "V146_SC_IPC_LEAF verified=1",
                     "V147_SC_IPC_NEXT verified=1",
                     'test "$(grep -Ec'):
            self.assertIn(gate,script)
        self.assertTrue(re.fullmatch(PASS,"V147_SC_IPC_NEXT first=1 caller=1 progressed=1 masked=1 queued=1 irq=1 target=8051906c lr=80519364"))
        self.assertFalse(re.fullmatch(PASS,"V147_SC_IPC_NEXT first=1 caller=0 progressed=1 masked=1 queued=1 irq=1 target=8051906c lr=80519364"))
        self.assertFalse(re.fullmatch(PASS,"V147_SC_IPC_NEXT first=1 caller=1 progressed=1 masked=1 queued=1 irq=1 target=8051906c lr=8052f930"))
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/"derived.sh";f.write_text(script)
            subprocess.run(["bash","-n",str(f)],check=True)

    def test_fail_closed_and_cleanup(self):
        with self.assertRaises(ValueError):derive("invalid")
        with self.assertRaises(ValueError):runner("invalid")
        wf=(HERE.parents[1]/".github/workflows/wii-v147-sc-ipc-next.yml").read_text()
        self.assertIn("run_v147_sc_ipc_next.sh",wf)
        self.assertIn("V147_SC_IPC_NEXT verified=1",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)

if __name__=="__main__":
    unittest.main()
