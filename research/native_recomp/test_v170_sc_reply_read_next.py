#!/usr/bin/env python3
"""Original-free V170 SC Y1 reply read next-call, SDA, and IRQ consistency tests."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v169_sc_reply_processor_harness import derive as previous
from derive_v170_sc_reply_read_next_harness import (
    derive, STATE, RESET, STOP, CONTINUE, OBSERVER,
    TRACE_ANCHOR, PREVIOUS_TRIAL, NEXT_TRIAL, PAIR, extend_prior_gates,
)
from derive_v170_sc_reply_read_next_runner import derive as runner, PASS
HERE=Path(__file__).resolve().parent

class V170(unittest.TestCase):
    def setUp(self):
        self.base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")

    def test_executes_only_original_v169_read_helper(self):
        before=previous(self.base)
        after=derive(self.base)
        for token in (STATE,RESET,STOP,TRACE_ANCHOR,PREVIOUS_TRIAL):
            self.assertEqual(before.count(token),1,token[:80])
        self.assertNotIn(STOP,after)
        self.assertIn(CONTINUE,after)
        self.assertIn(OBSERVER,after)
        self.assertIn(NEXT_TRIAL,after)
        self.assertIn("addr==0x8051905cu&&ctx.lr==0x805190e8u",CONTINUE)
        self.assertIn("return; // original guest IPC control-read instructions",CONTINUE)
        self.assertIn("ctx.inst_count>v170_start_inst",OBSERVER)
        self.assertIn("ctx.gpr[13]==v147_first_r13",OBSERVER)
        self.assertIn("ctx.lr>=0x805190c0u&&ctx.lr<0x80519318u",OBSERVER)
        self.assertIn("Mail::PPCCTRL",OBSERVER)
        self.assertIn("Mail::ARMMSG",OBSERVER)
        self.assertIn("Irq::IPC_PPC",OBSERVER)
        self.assertIn("ctx.mmu.get_ptr(sda)",OBSERVER)
        self.assertIn("ctx.mmu.read8(sda)",OBSERVER)
        self.assertIn("v170_target_pc=addr;v170_target_lr=ctx.lr",OBSERVER)
        self.assertEqual(after.count("V170_SC_REPLY_READ_NEXT guest="),1)

    def test_inherited_trial_state_is_still_required(self):
        after=derive(self.base)
        for label in (
            "V166 second SC reply nested interrupt restore did not reach real guest call",
            "V167 original SC reply IPC handler did not reach first real guest leaf",
            "V168 original SC Y1 register read did not reach second guest leaf",
            "V169 original SC reply processor did not reach next guest call",
        ):
            marker='"'+label+'");'
            self.assertEqual(after.count(marker),1)
            end=after.index(marker)
            start=after.rfind("check(",0,end)
            self.assertGreaterEqual(start,0)
            clause=after[start:end]
            for token in ("v170_next_seen==1u",
                          "c.pc==nwii::runtime::v170_target_pc",
                          "c.lr==nwii::runtime::v170_target_lr",
                          "!c.is_running"):
                self.assertIn(token,clause)
        self.assertIn("V170 original SC reply read helper did not reach next native guest call",after)
        self.assertTrue(PAIR.search("c.pc==nwii::runtime::v169_target_pc&&\n c.lr==nwii::runtime::v169_target_lr"))
        with self.assertRaises(ValueError):extend_prior_gates("invalid")

    def test_no_guest_or_hardware_mutations(self):
        before=previous(self.base)
        after=derive(self.base)
        for tok in ("ctx.mmu.write8(", "ctx.mmu.write16(", "ctx.mmu.write32(",
                    "ipc70_ram.write8(", "ipc70_bus.write32(",
                    "ipc70_bus.tick(", "scheduler.service_one(ctx.msr)",
                    "enter_external_irq("):
            self.assertEqual(before.count(tok),after.count(tok),tok)
        for pattern in (r"ctx\.gpr\[[^\]]+\]\s*=(?!=)",
                        r"ctx\.msr\s*=(?!=)",r"ctx\.srr0\s*=(?!=)",
                        r"ctx\.srr1\s*=(?!=)"):
            self.assertEqual(len(re.findall(pattern,before)),
                             len(re.findall(pattern,after)),pattern)

    def test_runner_and_private_cleanup(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for tok in ("derive_v170_sc_reply_read_next_harness.py",
                    "V168_SC_REPLY_NEXT verified=1",
                    "V169_SC_REPLY_NEXT verified=1",
                    "V170_SC_REPLY_READ_NEXT verified=1",
                    'test "$(grep -Ec'):
            self.assertIn(tok,script)
        valid=("V170_SC_REPLY_READ_NEXT guest=1 caller=1 coherent=1 mapped=1 "
               "y1=1 irq=1 reply=1 wire=1 status=1 read=0 write=1 "
               "pc=8051906c lr=805190fc")
        self.assertTrue(re.fullmatch(PASS,valid))
        self.assertFalse(re.fullmatch(PASS,valid.replace("coherent=1","coherent=0")))
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"runner.sh";path.write_text(script,encoding="utf-8")
            subprocess.run(["bash","-n",str(path)],check=True)
        with self.assertRaises(ValueError):derive("invalid")
        with self.assertRaises(ValueError):runner("invalid")
        wf=(HERE.parents[1]/".github/workflows/wii-v170-sc-reply-read-next.yml").read_text(encoding="utf-8")
        self.assertIn("run_v170_sc_reply_read_next.sh",wf)
        self.assertIn("V170_SC_REPLY_READ_NEXT verified=1",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)

if __name__=="__main__":
    unittest.main()
