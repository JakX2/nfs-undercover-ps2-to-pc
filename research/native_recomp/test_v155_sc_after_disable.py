#!/usr/bin/env python3
"""Original-free V155 guard: execute authentic SC OSDI call without invented state."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from derive_v154_sc_scheduler_next_harness import derive as previous
from derive_v155_sc_after_disable_harness import (
    derive, STATE, RESET, STOP, CONTINUE, NEXT_OBSERVER, NEXT_TRIAL,
    V146_ONCE, PREVIOUS_TRIAL,
)
from derive_v155_sc_after_disable_runner import derive as runner, PASS

HERE=Path(__file__).resolve().parent

class V155(unittest.TestCase):
    def setUp(self):
        self.source=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")

    def test_releases_only_authenticated_original_osdisable_call(self):
        prior=previous(self.source)
        new=derive(self.source)
        for anchor in (STATE,RESET,STOP,V146_ONCE,PREVIOUS_TRIAL):
            self.assertEqual(prior.count(anchor),1,anchor[:78])
        self.assertNotIn(STOP,new)
        self.assertIn(CONTINUE,new)
        self.assertIn(NEXT_OBSERVER,new)
        self.assertIn(NEXT_TRIAL,new)
        self.assertIn("addr==0x805265acu&&ctx.lr==0x80529448u",CONTINUE)
        self.assertIn("ctx.inst_count>v155_first_inst",NEXT_OBSERVER)
        self.assertIn("ctx.gpr[13]==v147_first_r13",NEXT_OBSERVER)
        self.assertIn("queued_replies()==0u",NEXT_OBSERVER)
        self.assertIn("V155Ios::Device::File",NEXT_OBSERVER)
        self.assertIn("V155Mail::Y1",NEXT_OBSERVER)
        self.assertIn("V155Irq::IPC_PPC",NEXT_OBSERVER)
        self.assertEqual(new.count("V155_SC_AFTER_DISABLE y1="),1)

    def test_no_mutated_guest_cpu_or_extra_ios_service_step(self):
        prior=previous(self.source)
        new=derive(self.source)
        for token in ("ctx.mmu.write8(", "ctx.mmu.write16(", "ctx.mmu.write32(",
                      "ipc70_ram.write8(", "ipc70_bus.write32(",
                      "scheduler.service_one(ctx.msr)", "ipc70_bus.tick(",
                      "v139_scheduler.service_one("):
            self.assertEqual(prior.count(token),new.count(token),token)
        for pattern in (r"ctx\.gpr\[[^\]]+\]\s*=(?!=)",
                        r"ctx\.cr\[0\]\.eq\s*=(?!=)",
                        r"ctx\.msr\s*=(?!=)"):
            self.assertEqual(len(re.findall(pattern,prior)),
                             len(re.findall(pattern,new)),pattern)
        self.assertIn("return; // execute original interrupt-disable guest function",CONTINUE)

    def test_16_owner_trials_retain_v154_and_v153(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for marker in ("derive_v155_sc_after_disable_harness.py",
                       "V153_SC_REPLY verified=1",
                       "V154_SC_SCHED_NEXT verified=1",
                       "V155_SC_AFTER_DISABLE verified=1",
                       'test "$(grep -Ec'):
            self.assertIn(marker,script)
        self.assertTrue(re.fullmatch(PASS,
            "V155_SC_AFTER_DISABLE y1=1 reply=1 progressed=1 call=1 pc=80529940 lr=80526cb4"))
        self.assertFalse(re.fullmatch(PASS,
            "V155_SC_AFTER_DISABLE y1=1 reply=0 progressed=1 call=1 pc=80529940 lr=80526cb4"))
        with tempfile.TemporaryDirectory() as temp:
            f=Path(temp)/"runner.sh"
            f.write_text(script,encoding="utf-8")
            subprocess.run(["bash","-n",str(f)],check=True)

    def test_fail_closed_and_private_cleanup(self):
        with self.assertRaises(ValueError):derive("invalid")
        with self.assertRaises(ValueError):runner("invalid")
        wf=(HERE.parents[1]/".github/workflows/wii-v155-sc-after-disable.yml").read_text(encoding="utf-8")
        self.assertIn("run_v155_sc_after_disable.sh",wf)
        self.assertIn("V155_SC_AFTER_DISABLE verified=1",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)

if __name__=="__main__":
    unittest.main()
