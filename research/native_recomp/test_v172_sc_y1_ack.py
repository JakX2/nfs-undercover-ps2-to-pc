#!/usr/bin/env python3
"""V172 original-free guest PPCCTRL Y1 W1C and Hollywood-latch ordering."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v171_sc_reply_distinct_harness import derive as previous
from derive_v172_sc_y1_ack_harness import (
    derive, STATE, RESET, STOP, CONTINUE, MMIO_ANCHOR,
    MMIO_OBSERVER, PREVIOUS_TRIAL, NEXT_TRIAL, PAIR, widen_prior_pc_gates,
    V153_MAIL_OLD, V153_MAIL_NEW,
)
from derive_v172_sc_y1_ack_runner import derive as runner, PASS
HERE=Path(__file__).resolve().parent

class V172(unittest.TestCase):
    def setUp(self):
        self.base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")

    def test_original_hardware_write_not_a_synthesized_ack(self):
        before=previous(self.base)
        after=derive(self.base)
        for token in (STATE,RESET,STOP,MMIO_ANCHOR,PREVIOUS_TRIAL):
            self.assertEqual(before.count(token),1,token[:72])
        self.assertNotIn(STOP,after)
        self.assertIn(CONTINUE,after)
        self.assertIn(MMIO_OBSERVER,after)
        self.assertEqual(before.count(V153_MAIL_OLD),1)
        self.assertNotIn(V153_MAIL_OLD,after)
        self.assertEqual(after.count(V153_MAIL_NEW),1)
        self.assertIn("v172_ack_seen==1u",V153_MAIL_NEW)
        self.assertIn("((*v153_ctrl&V153Mail::Y2)==0u)",V153_MAIL_NEW)
        self.assertIn("((*v153_flags&V153Irq::IPC_PPC)!=0u)",V153_MAIL_NEW)
        self.assertIn(NEXT_TRIAL,after)
        self.assertIn("addr==0x8051906cu&&ctx.lr==0x8051910cu",CONTINUE)
        self.assertIn("return; // execute original guest PPCCTRL writer",CONTINUE)
        for token in ("mmio_writes.emplace_back(addr,value)",
                      "(value&M::Y1)!=0u","((*control&M::Y1)==0u)",
                      "((*flag&H::IPC_PPC)!=0u)",
                      "ipc70_bus.external_irq_level()",
                      "ipc70_ram.cpu->lr==0x8051910cu",
                      "mmio_writes.size()>v172_writes_before",
                      "ipc70_ram.cpu->mmu.read8(sda)",
                      "v172_stop_pc=ipc70_ram.cpu->pc",
                      "v172_stop_lr=ipc70_ram.cpu->lr"):
            self.assertIn(token,MMIO_OBSERVER)
        self.assertEqual(after.count("V172_SC_Y1_ACK w1c="),1)

    def test_all_prior_pc_checkpoints_remain_authenticated(self):
        after=derive(self.base)
        for label in (
            "V166 second SC reply nested interrupt restore did not reach real guest call",
            "V167 original SC reply IPC handler did not reach first real guest leaf",
            "V168 original SC Y1 register read did not reach second guest leaf",
            "V169 original SC reply processor did not reach next guest call",
            "V170 original SC Y1 reply read did not reach next native function",
            "V171 original SC reply processor did not reach distinct native callee",
        ):
            marker='"'+label+'");'
            self.assertEqual(after.count(marker),1)
            end=after.index(marker)
            start=after.rfind("check(",0,end)
            self.assertGreaterEqual(start,0)
            text=after[start:end]
            self.assertIn("v172_ack_seen==1u",text)
            self.assertIn("c.pc==nwii::runtime::v172_stop_pc",text)
            self.assertIn("c.lr==nwii::runtime::v172_stop_lr",text)
            self.assertIn("!c.is_running",text)
        self.assertIn("V172 original SC Y1 reply PPCCTRL ACK was not performed by game code",after)
        self.assertTrue(PAIR.search("c.pc==nwii::runtime::v171_target_pc&&c.lr==nwii::runtime::v171_target_lr"))
        with self.assertRaises(ValueError):widen_prior_pc_gates("invalid")

    def test_no_new_host_ios_service_or_guest_cpu_mutation(self):
        before=previous(self.base)
        after=derive(self.base)
        for token in ("ctx.mmu.write8(", "ctx.mmu.write16(", "ctx.mmu.write32(",
                      "ipc70_ram.write8(", "ipc70_bus.write32(",
                      "ipc70_bus.tick(", "scheduler.service_one(ctx.msr)",
                      "enter_external_irq("):
            self.assertEqual(before.count(token),after.count(token),token)
        # Native bus MMIO writes are *existing* original guest operations:
        self.assertEqual(before.count("ipc70_bus.write32(addr,value)"),
                         after.count("ipc70_bus.write32(addr,value)"))
        for pat in (r"ctx\.gpr\[[^\]]+\]\s*=(?!=)",r"ctx\.msr\s*=(?!=)",
                    r"ctx\.srr0\s*=(?!=)",r"ctx\.srr1\s*=(?!=)"):
            self.assertEqual(len(re.findall(pat,before)),
                             len(re.findall(pat,after)),pat)

    def test_sixteen_real_original_trials_and_private_cleanup(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for token in ("derive_v172_sc_y1_ack_harness.py",
                      "V170_SC_REPLY_NEXT verified=1",
                      "V171_SC_DISTINCT verified=1",
                      "V172_SC_Y1_ACK verified=1",
                      'test "$(grep -Ec'):
            self.assertIn(token,script)
        good=("V172_SC_Y1_ACK w1c=1 flag=1 irq=1 wire=1 reply=1 "
              "guest=1 wrote=1 mapped=1 status=1 pc=8051906c lr=8051910c")
        self.assertTrue(re.fullmatch(PASS,good))
        self.assertFalse(re.fullmatch(PASS,good.replace("w1c=1","w1c=0")))
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/"run.sh";p.write_text(script,encoding="utf-8")
            subprocess.run(["bash","-n",str(p)],check=True)
        with self.assertRaises(ValueError):derive("invalid")
        with self.assertRaises(ValueError):runner("invalid")
        workflow=(HERE.parents[1]/".github/workflows/wii-v172-sc-y1-ack.yml").read_text(encoding="utf-8")
        self.assertIn("run_v172_sc_y1_ack.sh",workflow)
        self.assertIn("V172_SC_Y1_ACK verified=1",workflow)
        self.assertEqual(workflow.count("      - name: Remove private owner and generated code"),1)
if __name__=="__main__":
    unittest.main()
