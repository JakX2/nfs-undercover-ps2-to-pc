#!/usr/bin/env python3
"""V169 original-free Y1 reply processor successor and SDA observation guards."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v168_sc_reply_read_next_harness import derive as previous
from derive_v169_sc_reply_processor_harness import (
    derive, STATE, RESET, STOP, CONTINUE, OBSERVER, TRACE_ANCHOR,
    OLD_V79, SCOPED_V79, PREVIOUS_TRIAL, NEXT_TRIAL, PAIR,
    extend_old_trial_endpoints,
)
from derive_v169_sc_reply_processor_runner import derive as runner, PASS
HERE=Path(__file__).resolve().parent

class V169(unittest.TestCase):
    def setUp(self):
        self.base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")

    def test_original_reply_processor_and_status_byte_are_read_only(self):
        before=previous(self.base)
        after=derive(self.base)
        for anchor in (STATE,RESET,STOP,TRACE_ANCHOR,OLD_V79,PREVIOUS_TRIAL):
            self.assertEqual(before.count(anchor),1,anchor[:72])
        self.assertNotIn(STOP,after)
        self.assertIn(CONTINUE,after)
        self.assertIn(OBSERVER,after)
        self.assertIn(NEXT_TRIAL,after)
        self.assertIn(SCOPED_V79,after)
        self.assertNotIn(OLD_V79,after)
        self.assertIn("addr==0x805190c0u&&ctx.lr==0x80519354u",CONTINUE)
        self.assertIn("return; // execute original Wii reply processor code",CONTINUE)
        for token in ("ctx.inst_count>v169_start_inst","ctx.gpr[13]==v147_first_r13",
                      "ctx.lr>=0x80400000u&&ctx.lr<0x80600000u",
                      "ctx.mmu.get_ptr(sda)","ctx.mmu.read8(sda)",
                      "Mail::PPCCTRL","Mail::ARMMSG","IOS::Reply",
                      "v169_target_pc=addr;v169_target_lr=ctx.lr"):
            self.assertIn(token,OBSERVER)
        self.assertEqual(after.count("V169_SC_REPLY_NEXT guest="),1)

    def test_inherited_state_checks_preserved_while_allowing_next_pc(self):
        after=derive(self.base)
        for label in (
            "V166 second SC reply nested interrupt restore did not reach real guest call",
            "V167 original SC reply IPC handler did not reach first real guest leaf",
            "V168 original SC Y1 register read did not reach second guest leaf",
        ):
            marker='"'+label+'");'
            self.assertEqual(after.count(marker),1)
            end=after.index(marker)
            start=after.rfind("check(",0,end)
            self.assertGreaterEqual(start,0)
            sub=after[start:end]
            self.assertIn("v169_next_seen==1u",sub)
            self.assertIn("c.pc==nwii::runtime::v169_target_pc",sub)
            self.assertIn("c.lr==nwii::runtime::v169_target_lr",sub)
            self.assertIn("!c.is_running",sub)
        self.assertIn("V169 original SC reply processor did not reach next guest call",after)
        self.assertTrue(PAIR.search("c.pc==nwii::runtime::v168_target_pc&&\n c.lr==nwii::runtime::v168_target_lr"))
        with self.assertRaises(ValueError):extend_old_trial_endpoints("unrelated")

    def test_no_cpu_irq_or_ios_shortcuts(self):
        before=previous(self.base)
        after=derive(self.base)
        for token in ("ctx.mmu.write8(", "ctx.mmu.write16(", "ctx.mmu.write32(",
                      "ipc70_ram.write8(", "ipc70_bus.write32(",
                      "ipc70_bus.tick(", "scheduler.service_one(ctx.msr)",
                      "enter_external_irq("):
            self.assertEqual(before.count(token),after.count(token),token)
        for pattern in (r"ctx\.gpr\[[^\]]+\]\s*=(?!=)",r"ctx\.msr\s*=(?!=)",
                        r"ctx\.srr0\s*=(?!=)",r"ctx\.srr1\s*=(?!=)"):
            self.assertEqual(len(re.findall(pattern,before)),
                             len(re.findall(pattern,after)),pattern)

    def test_private_runner_needs_sixteen_and_secure_cleanup(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for needle in ("derive_v169_sc_reply_processor_harness.py",
                       "V166_SC_POST_RESTORE verified=1",
                       "V167_SC_REPLY_LEAF verified=1",
                       "V168_SC_REPLY_NEXT verified=1",
                       "V169_SC_REPLY_NEXT verified=1",
                       'test "$(grep -Ec'):
            self.assertIn(needle,script)
        valid=("V169_SC_REPLY_NEXT guest=1 caller=1 coherent=1 mapped=1 "
               "y1=0 flag=1 reply=1 wire=1 ready=0 status=1 "
               "read=0 write=1 pc=8051906c lr=80519358")
        self.assertTrue(re.fullmatch(PASS,valid))
        self.assertFalse(re.fullmatch(PASS,valid.replace("guest=1","guest=0")))
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"runner.sh";p.write_text(script,encoding="utf-8")
            subprocess.run(["bash","-n",str(p)],check=True)
        with self.assertRaises(ValueError):derive("invalid")
        with self.assertRaises(ValueError):runner("invalid")
        workflow=(HERE.parents[1]/".github/workflows/wii-v169-sc-reply-processor.yml").read_text(encoding="utf-8")
        self.assertIn("run_v169_sc_reply_processor.sh",workflow)
        self.assertIn("V169_SC_REPLY_NEXT verified=1",workflow)
        self.assertEqual(workflow.count("      - name: Remove private owner and generated code"),1)
if __name__=="__main__":
    unittest.main()
