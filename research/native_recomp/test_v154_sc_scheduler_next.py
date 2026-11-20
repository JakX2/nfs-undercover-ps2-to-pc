#!/usr/bin/env python3
"""Original-free V154 SC guest scheduler helper and Y1 reply preservation tests."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v153_sc_reply_handoff_harness import derive as previous
from derive_v154_sc_scheduler_next_harness import (
    derive, STATE, RESET, STOP, CONTINUE, OBSERVER,
    TRIAL, TRIAL_NEXT, V146_ONCE, V153_CHECK, V154_CHECK,
)
from derive_v154_sc_scheduler_next_runner import derive as runner, PASS

HERE=Path(__file__).resolve().parent

class V154(unittest.TestCase):
    def setUp(self):
        self.base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")

    def test_release_only_verified_sc_reply_stop(self):
        prior=previous(self.base)
        after=derive(self.base)
        self.assertEqual(prior.count(STOP),1)
        self.assertNotIn(STOP,after)
        self.assertIn(CONTINUE,after)
        self.assertEqual(after.count(OBSERVER),1)
        self.assertIn(TRIAL_NEXT,after)
        self.assertEqual(TRIAL.count(V153_CHECK),1)
        self.assertEqual(after.count(V153_CHECK),0)
        self.assertIn(V154_CHECK,after)
        self.assertIn("v153_phys=*req;v153_fd=uint32_t(result);",CONTINUE)
        self.assertIn("ctx.inst_count>v154_start_inst",OBSERVER)
        self.assertIn("v154_next_seen==1u",after)

    def test_guest_cpu_and_ios_state_are_not_fabricated(self):
        prior=previous(self.base)
        after=derive(self.base)
        for token in ("ctx.mmu.write8(", "ctx.mmu.write16(", "ctx.mmu.write32(",
                      "ipc70_ram.write8(", "ipc70_bus.write32(",
                      "scheduler.service_one(ctx.msr)", "ipc70_bus.tick("):
            self.assertEqual(prior.count(token),after.count(token),token)
        for pat in (r"ctx\.gpr\[[^\]]+\]\s*=(?!=)",
                    r"ctx\.cr\[0\]\.eq\s*=(?!=)",
                    r"ctx\.msr\s*=(?!=)"):
            self.assertEqual(len(re.findall(pat,prior)),len(re.findall(pat,after)),pat)
        for marker in ("V154Mail::Y1", "V154Mail::Y2",
                       "V154Irq::IPC_PPC", "queued_replies()==0u",
                       "V154Ios::Device::File",
                       "ctx.gpr[13]==v147_first_r13",
                       "ctx.inst_count>v154_start_inst"):
            self.assertIn(marker,OBSERVER)

    def test_runner_preserves_prior_ci_and_requires_sixteen(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for marker in ("derive_v154_sc_scheduler_next_harness.py",
                       "V153_SC_REPLY verified=1",
                       "V154_SC_SCHED_NEXT verified=1",
                       'test "$(grep -Ec'):
            self.assertIn(marker,script)
        self.assertTrue(re.fullmatch(PASS,
          "V154_SC_SCHED_NEXT signal=1 reply=1 guest=1 target=1 pc=805265d4 lr=80529448"))
        self.assertFalse(re.fullmatch(PASS,
          "V154_SC_SCHED_NEXT signal=0 reply=1 guest=1 target=1 pc=805265d4 lr=80529448"))
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/"derived.sh"
            p.write_text(script,encoding="utf-8")
            subprocess.run(["bash","-n",str(p)],check=True)

    def test_fail_closed_and_owner_cleanup(self):
        with self.assertRaises(ValueError):derive("invalid")
        with self.assertRaises(ValueError):runner("invalid")
        workflow=(HERE.parents[1]/".github/workflows/wii-v154-sc-scheduler-next.yml").read_text(encoding="utf-8")
        self.assertIn("run_v154_sc_scheduler_next.sh",workflow)
        self.assertIn("V154_SC_SCHED_NEXT verified=1",workflow)
        self.assertEqual(workflow.count("      - name: Remove private owner and generated code"),1)

if __name__=="__main__":
    unittest.main()
