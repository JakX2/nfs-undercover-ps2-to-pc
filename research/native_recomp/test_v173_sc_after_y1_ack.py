#!/usr/bin/env python3
"""V173 original-free Y1 ACK continuation and read-only SC status tests."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v172_sc_y1_ack_harness import derive as previous
from derive_v173_sc_after_y1_ack_harness import (
    derive, STATE, RESET, STOP, CONTINUE, OBSERVER,
    PREVIOUS_TRIAL, NEXT_TRIAL, V172_FINAL_END, V173_FINAL_END,
    V172_FINAL_EXTENDED, PAIR, widen_prior_gates,
    V173_V153_MAIL, V153_IRQ_NEW,
)
from derive_v173_sc_after_y1_ack_runner import derive as runner, PASS, HW_PASS
HERE=Path(__file__).resolve().parent

class V173(unittest.TestCase):
    def setUp(self):
        self.base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")

    def test_original_guest_y1_mmio_writer_resumes_to_next_call(self):
        before=previous(self.base)
        after=derive(self.base)
        for token in (STATE,RESET,STOP,PREVIOUS_TRIAL):
            self.assertEqual(before.count(token),1,token[:72])
        self.assertEqual(PREVIOUS_TRIAL.count(V172_FINAL_END),1)
        self.assertNotIn(STOP,after)
        self.assertIn(CONTINUE,after)
        self.assertIn(OBSERVER,after)
        self.assertIn(NEXT_TRIAL,after)
        self.assertIn(V173_FINAL_END,after)
        self.assertNotIn(V172_FINAL_EXTENDED,after)
        self.assertIn("v173_start_inst=ipc70_ram.cpu->inst_count",CONTINUE)
        self.assertIn("v173_mmio_after_y1=mmio_writes.size()",CONTINUE)
        self.assertIn("++v172_ack_seen",CONTINUE)
        self.assertNotIn("ipc70_ram.cpu->is_running=false",CONTINUE)
        self.assertIn("return to the *original* translated PPCCTRL writer",CONTINUE)
        self.assertIn("ctx.inst_count>v173_start_inst",OBSERVER)
        self.assertIn("ctx.gpr[13]==v147_first_r13",OBSERVER)
        self.assertIn("((*ctrl&Mail::Y1)==0u)",OBSERVER)
        self.assertIn("Mail::ARMMSG",OBSERVER)
        self.assertIn("Irq::IPC_PPC",OBSERVER)
        self.assertIn("ctx.mmu.read8(sda)",OBSERVER)
        self.assertIn("v173_target_pc=addr;v173_target_lr=ctx.lr",OBSERVER)
        self.assertEqual(after.count("V173_SC_AFTER_Y1_ACK y1clear="),1)
        self.assertIn("for(size_t i=v173_mmio_after_y1;i<mmio_writes.size();++i)",OBSERVER)
        self.assertIn("write.first==Bus::IPC+Irq::PPC_FLAG",OBSERVER)
        self.assertIn("write.second&Irq::IPC_PPC",OBSERVER)
        self.assertIn("check(flag_ack,",OBSERVER)
        self.assertIn("++v173_flag_ack_seen;",OBSERVER)
        self.assertEqual(after.count("V173_SC_HW_FLAG_W1C guest=1 count="),1)
        self.assertIn(V173_V153_MAIL,after)
        self.assertIn(V153_IRQ_NEW,after)
        self.assertIn("v173_flag_ack_seen==1u",NEXT_TRIAL)

    def test_prior_native_end_checks_retained(self):
        after=derive(self.base)
        for label in (
            "V166 second SC reply nested interrupt restore did not reach real guest call",
            "V167 original SC reply IPC handler did not reach first real guest leaf",
            "V168 original SC Y1 register read did not reach second guest leaf",
            "V169 original SC reply processor did not reach next guest call",
            "V170 original SC Y1 reply read did not reach next native function",
            "V171 original SC reply processor did not reach distinct native callee",
            "V172 original SC Y1 reply PPCCTRL ACK was not performed by game code",
        ):
            marker='"'+label+'");'
            self.assertEqual(after.count(marker),1)
            end=after.index(marker)
            start=after.rfind("check(",0,end)
            snippet=after[start:end]
            self.assertIn("v173_next_seen==1u",snippet)
            self.assertIn("!c.is_running",snippet)
        self.assertIn("V173 original SYSCONF Y1 reply W1C did not advance to next guest call",after)
        self.assertTrue(PAIR.search("c.pc==nwii::runtime::v172_stop_pc&&\n c.lr==nwii::runtime::v172_stop_lr"))
        with self.assertRaises(ValueError):widen_prior_gates("invalid")

    def test_no_undocumented_cpu_or_ios_writes(self):
        before=previous(self.base)
        after=derive(self.base)
        for tok in ("ctx.mmu.write8(", "ctx.mmu.write16(", "ctx.mmu.write32(",
                    "ipc70_ram.write8(", "ipc70_bus.write32(",
                    "scheduler.service_one(ctx.msr)", "ipc70_bus.tick(",
                    "enter_external_irq("):
            self.assertEqual(before.count(tok),after.count(tok),tok)
        for regex in (r"ctx\.gpr\[[^\]]+\]\s*=(?!=)",
                      r"ctx\.msr\s*=(?!=)",
                      r"ctx\.srr0\s*=(?!=)",r"ctx\.srr1\s*=(?!=)"):
            self.assertEqual(len(re.findall(regex,before)),
                             len(re.findall(regex,after)),regex)

    def test_owner_runner_sixteen_and_private_cleanup(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for token in ("derive_v173_sc_after_y1_ack_harness.py",
                      "V171_SC_DISTINCT verified=1",
                      "V172_SC_Y1_ACK verified=1",
                      "V173_SC_AFTER_Y1_ACK verified=1",
                      'test "$(grep -Ec'):
            self.assertIn(token,script)
        good=("V173_SC_AFTER_Y1_ACK y1clear=1 flag=1 wire=1 reply=1 "
              "guest=1 caller=1 coherent=1 mapped=1 status=1 "
              "read=1 write=0 pc=8051905c lr=80519128")
        self.assertTrue(re.fullmatch(PASS,good))
        self.assertEqual(HW_PASS,
            "V173_SC_HW_FLAG_W1C guest=1 count=1 cleared=1 irq_down=1")
        self.assertIn("grep -Fx '{HW_PASS}'",script)
        self.assertFalse(re.fullmatch(PASS,good.replace("y1clear=1","y1clear=0")))
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"run.sh";p.write_text(script,encoding="utf-8")
            subprocess.run(["bash","-n",str(p)],check=True)
        with self.assertRaises(ValueError):derive("invalid")
        with self.assertRaises(ValueError):runner("invalid")
        wf=(HERE.parents[1]/".github/workflows/wii-v173-sc-after-y1-ack.yml").read_text(encoding="utf-8")
        self.assertIn("run_v173_sc_after_y1_ack.sh",wf)
        self.assertIn("V173_SC_AFTER_Y1_ACK verified=1",wf)
        self.assertIn("V173_SC_HW_FLAG_W1C guest=1 count=1 cleared=1 irq_down=1",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)

if __name__=="__main__":
    unittest.main()
