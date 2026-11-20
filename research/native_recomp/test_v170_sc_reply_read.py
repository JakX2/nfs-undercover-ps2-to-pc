#!/usr/bin/env python3
"""V170 original-free SC Y1 processor read successor and status tests."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v169_sc_reply_processor_harness import derive as previous
from derive_v170_sc_reply_read_harness import (
    derive, STATE, RESET, STOP, CONTINUE, OBSERVER, TRACE_ANCHOR,
    PREVIOUS_TRIAL, NEXT_TRIAL, PAIR, widen_trial_endpoints,
)
from derive_v170_sc_reply_read_runner import derive as runner, PASS
HERE=Path(__file__).resolve().parent

class V170(unittest.TestCase):
    def setUp(self):
        self.base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")

    def test_original_reply_processor_guest_read_and_sda_observation(self):
        old=previous(self.base)
        new=derive(self.base)
        for oldpart in (STATE,RESET,STOP,TRACE_ANCHOR,PREVIOUS_TRIAL):
            self.assertEqual(old.count(oldpart),1,oldpart[:64])
        self.assertNotIn(STOP,new)
        self.assertIn(CONTINUE,new)
        self.assertIn(OBSERVER,new)
        self.assertIn(NEXT_TRIAL,new)
        self.assertIn("addr==0x8051905cu&&ctx.lr==0x805190e8u",CONTINUE)
        self.assertIn("return; // execute the original guest IPC reply control-read instructions",CONTINUE)
        for needle in ("ctx.inst_count>v170_start_inst",
                       "ctx.gpr[13]==v147_first_r13",
                       "ctx.mmu.get_ptr(sc_addr)","ctx.mmu.read8(sc_addr)",
                       "const bool changed=mapped&&status!=1u",
                       "Mail::PPCCTRL","Mail::ARMMSG","IOS::Reply",
                       "Irq::IPC_PPC","v170_target_pc=addr;v170_target_lr=ctx.lr"):
            self.assertIn(needle,OBSERVER)
        self.assertEqual(new.count("V170_SC_REPLY_NEXT guest="),1)

    def test_all_inherited_native_checkpoints_accept_only_new_stop_pair(self):
        new=derive(self.base)
        for label in (
            "V166 second SC reply nested interrupt restore did not reach real guest call",
            "V167 original SC reply IPC handler did not reach first real guest leaf",
            "V168 original SC Y1 register read did not reach second guest leaf",
            "V169 original SC reply processor did not reach next guest call",
        ):
            marker='"'+label+'");'
            self.assertEqual(new.count(marker),1)
            end=new.index(marker)
            start=new.rfind("check(",0,end)
            self.assertGreaterEqual(start,0)
            check=new[start:end]
            self.assertIn("v170_next_seen==1u",check)
            self.assertIn("c.pc==nwii::runtime::v170_target_pc",check)
            self.assertIn("c.lr==nwii::runtime::v170_target_lr",check)
            self.assertIn("!c.is_running",check)
        self.assertIn("V170 original SC Y1 reply read did not reach next native function",new)
        with self.assertRaises(ValueError):widen_trial_endpoints("invalid")
        self.assertTrue(PAIR.search("c.pc==nwii::runtime::v169_target_pc&&\n c.lr==nwii::runtime::v169_target_lr"))

    def test_cpu_ios_irq_are_not_synthetically_modified(self):
        old=previous(self.base)
        new=derive(self.base)
        for marker in ("ctx.mmu.write8(", "ctx.mmu.write16(", "ctx.mmu.write32(",
                       "ipc70_ram.write8(", "ipc70_bus.write32(",
                       "ipc70_bus.tick(", "scheduler.service_one(ctx.msr)",
                       "enter_external_irq("):
            self.assertEqual(old.count(marker),new.count(marker),marker)
        for pat in (r"ctx\.gpr\[[^\]]+\]\s*=(?!=)",r"ctx\.msr\s*=(?!=)",
                    r"ctx\.srr0\s*=(?!=)",r"ctx\.srr1\s*=(?!=)"):
            self.assertEqual(len(re.findall(pat,old)),len(re.findall(pat,new)),pat)

    def test_owner_private_runner_requires_sixteen_and_cleanup(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for marker in ("derive_v170_sc_reply_read_harness.py",
                       "V168_SC_REPLY_NEXT verified=1",
                       "V169_SC_REPLY_NEXT verified=1",
                       "V170_SC_REPLY_NEXT verified=1",
                       'test "$(grep -Ec'):
            self.assertIn(marker,script)
        text=("V170_SC_REPLY_NEXT guest=1 caller=1 coherent=1 mapped=1 "
              "y1=1 flag=1 reply=1 wire=1 ready=0 status=1 changed=0 "
              "read=0 write=1 pc=8051906c lr=80519104")
        self.assertTrue(re.fullmatch(PASS,text))
        self.assertFalse(re.fullmatch(PASS,text.replace("guest=1","guest=0")))
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"run.sh";p.write_text(script,encoding="utf-8")
            subprocess.run(["bash","-n",str(p)],check=True)
        with self.assertRaises(ValueError):derive("invalid")
        with self.assertRaises(ValueError):runner("invalid")
        wf=(HERE.parents[1]/".github/workflows/wii-v170-sc-reply-read.yml").read_text(encoding="utf-8")
        self.assertIn("run_v170_sc_reply_read.sh",wf)
        self.assertIn("V170_SC_REPLY_NEXT verified=1",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)

if __name__=="__main__":
    unittest.main()
