#!/usr/bin/env python3
"""Original-free V149 checks: authentic SC IPC PPCCTRL Y2 acknowledgment."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v148_sc_ipc_distinct_harness import derive as previous
from derive_v149_sc_ipc_ack_harness import (
    derive, STATE, RESET, STOP, CONTINUE, MMIO_OLD, MMIO_NEW, NEXT_TRIAL,
)
from derive_v149_sc_ipc_ack_runner import derive as runner, PASS
HERE=Path(__file__).resolve().parent

class V149(unittest.TestCase):
    def setUp(self):
        self.original=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")

    def test_guest_code_and_inherited_mmio_handler_preserved(self):
        before=previous(self.original)
        after=derive(self.original)
        for marker in (STATE,RESET,STOP,MMIO_OLD):
            self.assertEqual(before.count(marker),1,marker[:64])
        self.assertIn(CONTINUE,after)
        self.assertIn(MMIO_NEW,after)
        self.assertIn(NEXT_TRIAL,after)
        self.assertEqual(after.count("V149_SC_IPC_ACK write=1 w1c="),1)
        self.assertIn("addr==0x8051906cu&&ctx.lr==0x80519380u",CONTINUE)
        self.assertIn("check(ipc70_bus.write32(addr,value)",MMIO_NEW)
        self.assertIn("mmio_writes.emplace_back(addr,value);",MMIO_NEW)
        self.assertIn("control.has_value()",MMIO_NEW)
        self.assertIn("((*control&M::Y2)==0u)",MMIO_NEW)
        self.assertIn("ipc70_bus.services().queued_replies()==1u",MMIO_NEW)
        self.assertIn("throw ExceptionStop{};",MMIO_NEW)

    def test_no_extra_guest_mutations_or_ios_success_fabrication(self):
        old=previous(self.original)
        new=derive(self.original)
        for expr in ("ctx.mmu.write8(", "ctx.mmu.write32(", "ctx.mmu.write16(",
                     "ipc70_ram.write8(", "ipc70_bus.write32(",
                     "ipc70_bus.tick(", "v139_scheduler.service_one("):
            self.assertEqual(new.count(expr),old.count(expr),expr)
        for pat in (r"ctx\.gpr\[[^\]]+\]\s*=(?!=)",
                    r"ctx\.cr\[0\]\.eq\s*=(?!=)",
                    r"ctx\.msr\s*=(?!=)"):
            self.assertEqual(len(re.findall(pat,new)),len(re.findall(pat,old)),pat)
        self.assertNotIn("ipc70_ram.cpu->mmu.write",MMIO_NEW)

    def test_sixteen_native_trial_gate(self):
        text=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for tok in ("derive_v149_sc_ipc_ack_harness.py",
                    "V148_SC_IPC_DISTINCT verified=1",
                    "V149_SC_IPC_ACK verified=1",
                    'test "$(grep -Fxc'):
            self.assertIn(tok,text)
        self.assertEqual(PASS,"V149_SC_IPC_ACK write=1 w1c=1 queued=1 irq=1 guest=1")
        with tempfile.TemporaryDirectory() as td:
            file=Path(td)/"runner.sh";file.write_text(text)
            subprocess.run(["bash","-n",str(file)],check=True)

    def test_fail_closed_and_cleanup(self):
        with self.assertRaises(ValueError):derive("invalid")
        with self.assertRaises(ValueError):runner("invalid")
        wf=(HERE.parents[1]/".github/workflows/wii-v149-sc-ipc-ack.yml").read_text()
        self.assertIn("run_v149_sc_ipc_ack.sh",wf)
        self.assertIn("V149_SC_IPC_ACK verified=1",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)

if __name__=="__main__":
    unittest.main()
