#!/usr/bin/env python3
"""Original-free V150 native SC Hollywood IRQ flag write regression tests."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v149_sc_ipc_ack_harness import derive as previous
from derive_v150_sc_irq_flag_harness import (
    derive, STATE, RESET, V146_OBSERVER, V146_ONCE,
    MMIO_STOP, MMIO_CONTINUE, NEXT_TRIAL,
)
from derive_v150_sc_irq_flag_runner import derive as runner, PASS
HERE=Path(__file__).resolve().parent

class V150(unittest.TestCase):
    def setUp(self):
        self.base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")

    def test_first_leaf_observer_is_phase_scoped(self):
        before=previous(self.base)
        after=derive(self.base)
        self.assertEqual(before.count(V146_OBSERVER),1)
        self.assertEqual(after.count(V146_OBSERVER),0)
        self.assertEqual(after.count(V146_ONCE),1)
        self.assertIn("v146_leaf_seen==0u",V146_ONCE)
        for m in (STATE,RESET,MMIO_STOP):
            self.assertEqual(before.count(m),1,m[:50])
        self.assertIn(MMIO_CONTINUE,after)
        self.assertIn(NEXT_TRIAL,after)

    def test_ack_and_hollywood_semantics_are_observed_not_faked(self):
        prior=previous(self.base)
        now=derive(self.base)
        for fragment in ("check(ipc70_bus.write32(addr,value)",
                         "mmio_writes.emplace_back(addr,value);"):
            self.assertIn(fragment,now)
        for phrase in ("addr==B::IPC+H::PPC_FLAG",
                       "(value&H::IPC_PPC)!=0u",
                       "((*flags&H::IPC_PPC)==0u)",
                       "((*ctrl&M::Y2)==0u)",
                       "!ipc70_bus.external_irq_level()",
                       "ipc70_bus.services().queued_replies()==1u",
                       "V150_SC_IRQ_CLEAR write=1 w1c="):
            self.assertIn(phrase,MMIO_CONTINUE)
        for t in ("ctx.mmu.write8(", "ctx.mmu.write32(", "ctx.mmu.write16(",
                  "ipc70_ram.write8(", "ipc70_bus.write32(",
                  "ipc70_bus.tick(", "v139_scheduler.service_one("):
            self.assertEqual(now.count(t),prior.count(t),t)
        for p in (r"ctx\.gpr\[[^\]]+\]\s*=(?!=)",
                  r"ctx\.cr\[0\]\.eq\s*=(?!=)",
                  r"ctx\.msr\s*=(?!=)"):
            self.assertEqual(len(re.findall(p,now)),len(re.findall(p,prior)),p)
        self.assertEqual(now.count("V150_SC_IRQ_CLEAR write=1 w1c="),1)

    def test_private_native_regression_gate(self):
        s=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for marker in ("derive_v150_sc_irq_flag_harness.py",
                       "V149_SC_IPC_ACK verified=1",
                       "V150_SC_IRQ_CLEAR verified=1",
                       'test "$(grep -Fxc'):
            self.assertIn(marker,s)
        self.assertEqual(PASS,"V150_SC_IRQ_CLEAR write=1 w1c=1 ctrl=1 irq_down=1 queued=1 guest=1")
        with tempfile.TemporaryDirectory() as tmp:
            f=Path(tmp)/"run.sh";f.write_text(s)
            subprocess.run(["bash","-n",str(f)],check=True)

    def test_fail_closed_and_private_cleanup(self):
        with self.assertRaises(ValueError):derive("invalid")
        with self.assertRaises(ValueError):runner("invalid")
        wf=(HERE.parents[1]/".github/workflows/wii-v150-sc-irq-flag.yml").read_text()
        self.assertIn("run_v150_sc_irq_flag.sh",wf)
        self.assertIn("V150_SC_IRQ_CLEAR verified=1",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)

if __name__=="__main__":
    unittest.main()
