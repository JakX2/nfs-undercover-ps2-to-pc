#!/usr/bin/env python3
"""V153 original-free tests for SC hardware ACK -> queued native IOS reply bridge."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from derive_v152_sc_post_helper_harness import derive as previous
from derive_v153_sc_reply_handoff_harness import (
    derive, OBSERVER, NEXT_OBSERVER, NEXT_TRIAL,
    STATE, RESET, TRIAL,
)
from derive_v153_sc_reply_handoff_runner import derive as runner, PASS, PRE_PATTERN

HERE=Path(__file__).resolve().parent


class V153(unittest.TestCase):
    def setUp(self):
        self.source=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")

    def test_delegates_at_exact_authentic_post_irq_boundary(self):
        earlier=previous(self.source)
        now=derive(self.source)
        for marker in (OBSERVER,TRIAL,STATE,RESET):
            self.assertEqual(earlier.count(marker),1,marker[:72])
        self.assertIn(NEXT_OBSERVER,now)
        self.assertIn(NEXT_TRIAL,now)
        self.assertNotIn(OBSERVER,now)
        self.assertIn("addr==POST_OWNER&&ctx.lr==0x80526cb0u",NEXT_OBSERVER)
        self.assertIn("queued_replies()==1u",NEXT_OBSERVER)
        self.assertIn("const bool v153_queued=",NEXT_OBSERVER)
        self.assertIn("cleared&&v153_queued&&",NEXT_OBSERVER)
        self.assertEqual(NEXT_OBSERVER.count("const bool queued="),1)
        self.assertIn("scheduler.service_one(ctx.msr)",NEXT_OBSERVER)
        self.assertIn("V153Ios::Device::File",NEXT_OBSERVER)
        self.assertIn("ctx.is_running=false;throw ExceptionStop{};",NEXT_OBSERVER)
        self.assertIn("++v153_bridge_seen;",NEXT_OBSERVER)
        self.assertEqual(now.count("V153_SC_REPLY route="),1)
        self.assertEqual(now.count("V153_SC_REPLY_STATE bridge="),1)

    def test_no_extra_guest_or_device_changes(self):
        earlier=previous(self.source)
        now=derive(self.source)
        for token in ("ctx.mmu.write8(", "ctx.mmu.write16(", "ctx.mmu.write32(",
                      "ipc70_ram.write8(", "ipc70_bus.write32(",
                      "ipc70_bus.tick(", "v139_scheduler.service_one("):
            self.assertEqual(earlier.count(token),now.count(token),token)
        self.assertEqual(now.count("scheduler.service_one(ctx.msr)"),
                         earlier.count("scheduler.service_one(ctx.msr)")+1)
        self.assertIn("V153Ios::Pump::Replied",NEXT_OBSERVER)
        for pattern in (r"ctx\.gpr\[[^\]]+\]\s*=(?!=)",
                        r"ctx\.cr\[0\]\.eq\s*=(?!=)",
                        r"ctx\.msr\s*=(?!=)"):
            self.assertEqual(len(re.findall(pattern,earlier)),
                             len(re.findall(pattern,now)),pattern)
        for token in ("V153Ios::Reply","V153Ios::Open",
                      "queued_replies()==0u","V153Mail::Y1",
                      "V153Irq::IPC_PPC","!nwii::runtime::ipc70_bus.external_exception_pending(c.msr)"):
            self.assertIn(token,NEXT_TRIAL)

    def test_runner_gates_sixteen_and_previous_milestones(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for marker in ("derive_v153_sc_reply_handoff_harness.py",
                       "V150_SC_IRQ_CLEAR verified=1",
                       "V151_SC_AFTER_FLAG verified=1",
                       "V152_SC_POST_HELPER verified=1",
                       "V153_SC_REPLY verified=1",
                       'test "$(grep -Fxc'):
            self.assertIn(marker,script)
        self.assertEqual(PASS,"V153_SC_REPLY route=1 cleared=1 service=1 wire=1 fd=1 signal=1")
        self.assertIn(PRE_PATTERN,script)
        self.assertTrue(re.fullmatch(PRE_PATTERN,
            "V153_SC_PRE route=1 present=1 aligned=1 mapped=1 open=1 prior=1 same=1 clear=1 queued=1 masked=1"))
        self.assertFalse(re.fullmatch(PRE_PATTERN,
            "V153_SC_PRE addr=80420000 route=1 present=1 aligned=1 mapped=1 open=1 prior=1 same=1 clear=1 queued=1 masked=1"))
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/"run.sh"
            f.write_text(script,encoding="utf-8")
            subprocess.run(["bash","-n",str(f)],check=True)

    def test_missing_source_fails_closed_and_workflow_cleans_private_owner(self):
        with self.assertRaises(ValueError):derive("invalid")
        with self.assertRaises(ValueError):runner("invalid")
        wf=(HERE.parents[1]/".github/workflows/wii-v153-sc-reply-handoff.yml").read_text(encoding="utf-8")
        self.assertIn("run_v153_sc_reply_handoff.sh",wf)
        self.assertIn("V153_SC_REPLY verified=1",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)

if __name__=="__main__":
    unittest.main()
