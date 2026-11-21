#!/usr/bin/env python3
"""Source-only third negative IOS Y1 hardware-read successor V222."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v221_sc_y1_ipc_leaf_harness import derive as previous, OBSERVER as PREVIOUS_OBSERVER, NEXT_END as PREVIOUS_END
from derive_v222_sc_y1_ipc_next_harness import derive, STOP, CONTINUE, OBSERVER, NEXT_END
from derive_v222_sc_y1_ipc_next_runner import derive as runner, PATTERN, PASS
HERE=Path(__file__).resolve().parent

class V222(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=previous(base);cls.after=derive(base)

    def test_second_authentic_guest_callee(self):
        self.assertIn(STOP,PREVIOUS_OBSERVER)
        self.assertNotIn(STOP,self.after)
        self.assertIn(CONTINUE,self.after)
        self.assertIn(OBSERVER,self.after)
        self.assertIn(NEXT_END,self.after)
        self.assertNotIn(PREVIOUS_END,self.after)
        for name in ("v221_leaf_seen==1u","v222_next_seen==0u",
                     "ctx.lr>=0x80519318u&&ctx.lr<0x805194c4u",
                     "ctx.inst_count>v222_first_inst",
                     "int32_t(ipc70_ram.read32(v183_second_phys+4u))==IOS::Invalid",
                     "++v222_next_seen"):
            self.assertIn(name,OBSERVER)
        with self.assertRaises(ValueError):derive("wrong original fixture")

    def test_no_synthetic_success_or_guest_register_assignment(self):
        for name in ("scheduler.service_one(","ipc70_ram.write8(",
                     "ipc70_bus.write32(","ctx.mmu.write32("):
            self.assertEqual(self.before.count(name),self.after.count(name))
        for snippet in (CONTINUE,OBSERVER,NEXT_END):
            for forbidden in ("ipc70_bus.write","ipc70_ram.write",
                              "ctx.mmu.write","ctx.pc=0x"):
                self.assertNotIn(forbidden,snippet)
            self.assertNotRegex(snippet,r"ctx\.gpr\[[0-9]+\]\s*=(?!=)")

    def test_owner_trial_count_gate_and_private_cleanup(self):
        runner_script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for required in ("derive_v222_sc_y1_ipc_next_harness.py",
                         "V221_SC_Y1_IPC_LEAF verified=1",
                         "V222_SC_Y1_IPC_NEXT verified=1"):
            self.assertIn(required,runner_script)
        example="V222_NEG_NEXT guest=1 caller=1 reply=1 masked=1 coherent=1 irq=0 sc=1 pc=8051905c lr=8051935c"
        self.assertIsNotNone(re.fullmatch(PASS,example))
        self.assertIsNone(re.fullmatch(PASS,example.replace("reply=1","reply=0")))
        self.assertIsNotNone(re.fullmatch(PATTERN,example.replace("coherent=1","coherent=0")))
        wf=(HERE.parents[1]/".github/workflows/wii-v222-sc-y1-ipc-next.yml").read_text()
        for required in ("run_v222_sc_y1_ipc_next.sh",
                         "test_v222_sc_y1_ipc_next.py",
                         "V222_SC_Y1_IPC_NEXT verified=1"):
            self.assertIn(required,wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)
        with tempfile.TemporaryDirectory() as folder:
            for name,content in (("runner",runner_script),
                                 ("entry",(HERE/"run_v222_sc_y1_ipc_next.sh").read_text())):
                p=Path(folder)/name
                p.write_text(content,encoding="utf-8")
                subprocess.run(["bash","-n",str(p)],check=True)

if __name__=="__main__":
    unittest.main()
