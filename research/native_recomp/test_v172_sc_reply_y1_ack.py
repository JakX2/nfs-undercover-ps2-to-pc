#!/usr/bin/env python3
"""V172 original-free Y1 PPCCTRL write-one-to-clear + independent IRQ latch."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from derive_v171_sc_reply_distinct_harness import derive as previous
from derive_v172_sc_reply_y1_ack_harness import (
    derive, STATE, RESET, STOP, CONTINUE, ACK, MMIO_ANCHOR,
    PREVIOUS_TRIAL, NEXT_TRIAL, PAIR, add_ack_observer, extend_earlier_gates,
)
from derive_v172_sc_reply_y1_ack_runner import derive as runner, PASS
HERE=Path(__file__).resolve().parent

class V172(unittest.TestCase):
    def setUp(self):
        self.base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")

    def test_original_reply_writer_performs_authenticated_bus_w1c(self):
        before=previous(self.base)
        after=derive(self.base)
        for token in (STATE,RESET,STOP,PREVIOUS_TRIAL,MMIO_ANCHOR):
            self.assertEqual(before.count(token),1,token[:74])
        self.assertNotIn(STOP,after)
        self.assertIn(CONTINUE,after)
        self.assertIn(ACK,after)
        self.assertIn(NEXT_TRIAL,after)
        self.assertIn("addr==0x8051906cu&&ctx.lr==0x8051910cu",CONTINUE)
        self.assertIn("return; // run actual Wii PPC IPC control-store helper",CONTINUE)
        self.assertIn("if(v171_distinct_seen==1u&&v172_y1_ack_seen==0u",ACK)
        self.assertIn("(value&M::Y1)!=0u",ACK)
        self.assertIn("((*control&M::Y1)==0u)",ACK)
        self.assertIn("HollywoodIrq::IPC_PPC",ACK)
        self.assertIn("ipc70_bus.external_irq_level()",ACK)
        self.assertIn("ipc70_ram.cpu->lr==0x8051910cu",ACK)
        self.assertIn("ipc70_ram.cpu->gpr[13]==v147_first_r13",ACK)
        self.assertIn("ipc70_ram.cpu->is_running=false",ACK)
        self.assertIn("ctx.is_running=false",after)
        self.assertIn("ctx.mmu.read8(",after)
        self.assertEqual(after.count("V172_SC_REPLY_Y1_ACK write="),1)

    def test_callback_does_not_replace_original_writes(self):
        before=previous(self.base)
        after=derive(self.base)
        self.assertEqual(before.count("ipc70_bus.write32("),after.count("ipc70_bus.write32("))
        self.assertEqual(before.count("mmio_writes.emplace_back("),after.count("mmio_writes.emplace_back("))
        for token in ("ctx.mmu.write8(", "ctx.mmu.write16(", "ctx.mmu.write32(",
                      "ipc70_ram.write8(", "ipc70_bus.tick(",
                      "scheduler.service_one(ctx.msr)", "enter_external_irq("):
            self.assertEqual(before.count(token),after.count(token),token)
        for pattern in (r"ctx\.gpr\[[^\]]+\]\s*=(?!=)",
                        r"ctx\.msr\s*=(?!=)",r"ctx\.srr0\s*=(?!=)",
                        r"ctx\.srr1\s*=(?!=)"):
            self.assertEqual(len(re.findall(pattern,before)),
                             len(re.findall(pattern,after)),pattern)

    def test_prior_guest_state_checkpoints_are_not_deleted(self):
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
            snippet=after[start:end]
            self.assertIn("v172_y1_ack_seen==1u",snippet)
            self.assertIn("!c.is_running",snippet)
        self.assertTrue(PAIR.search("c.pc==nwii::runtime::v171_target_pc&&\n c.lr==nwii::runtime::v171_target_lr"))
        with self.assertRaises(ValueError):extend_earlier_gates("invalid")
        with self.assertRaises(ValueError):add_ack_observer("invalid")

    def test_private_runner_proves_sixteen_and_secure_cleanup(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for token in ("derive_v172_sc_reply_y1_ack_harness.py",
                      "V169_SC_REPLY_NEXT verified=1",
                      "V170_SC_REPLY_NEXT verified=1",
                      "V171_SC_DISTINCT verified=1",
                      "V172_SC_REPLY_Y1_ACK verified=1",
                      'test "$(grep -Ec'):
            self.assertIn(token,script)
        valid=("V172_SC_REPLY_Y1_ACK write=1 cleared=1 latched=1 guest=1 "
               "reply=1 mapped=1 status=1")
        self.assertTrue(re.fullmatch(PASS,valid))
        self.assertFalse(re.fullmatch(PASS,valid.replace("cleared=1","cleared=0")))
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"runner.sh";path.write_text(script,encoding="utf-8")
            subprocess.run(["bash","-n",str(path)],check=True)
        with self.assertRaises(ValueError):derive("invalid")
        with self.assertRaises(ValueError):runner("invalid")
        wf=(HERE.parents[1]/".github/workflows/wii-v172-sc-reply-y1-ack.yml").read_text(encoding="utf-8")
        self.assertIn("run_v172_sc_reply_y1_ack.sh",wf)
        self.assertIn("V172_SC_REPLY_Y1_ACK verified=1",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)

if __name__=="__main__":
    unittest.main()
