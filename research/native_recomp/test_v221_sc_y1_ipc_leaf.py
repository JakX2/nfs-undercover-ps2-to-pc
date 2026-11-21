#!/usr/bin/env python3
"""V221 original-free third negative IOS Y1 handler first helper tests."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v220_sc_y1_ipc_handler_harness import derive as previous, OBSERVER as PREVIOUS_OBSERVER, NEXT_END as PREVIOUS_END
from derive_v221_sc_y1_ipc_leaf_harness import derive, STOP, CONTINUE, OBSERVER, NEXT_END
from derive_v221_sc_y1_ipc_leaf_runner import derive as runner, PATTERN, PASS
HERE=Path(__file__).resolve().parent

class V221(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=previous(base)
        cls.after=derive(base)

    def test_first_authentic_ipc_hardware_helper(self):
        self.assertIn(STOP,PREVIOUS_OBSERVER)
        self.assertNotIn(STOP,self.after)
        self.assertIn(CONTINUE,self.after)
        self.assertIn(OBSERVER,self.after)
        self.assertIn(NEXT_END,self.after)
        self.assertNotIn(PREVIOUS_END,self.after)
        for needle in ("v220_ipc_seen==1u","addr==0x8051905cu",
                       "ctx.lr>=0x80519318u","ctx.inst_count>v221_ipc_inst",
                       "int32_t(ipc70_ram.read32(v183_second_phys+4u))==IOS::Invalid",
                       "++v221_leaf_seen"):
            self.assertIn(needle,OBSERVER)
        self.assertIn("v221_leaf_seen==1u",NEXT_END)
        with self.assertRaises(ValueError):
            derive("not the original fixture")

    def test_original_guest_state_read_only(self):
        for needle in ("scheduler.service_one(","ipc70_ram.write8(",
                       "ipc70_bus.write32(","ctx.mmu.write32("):
            self.assertEqual(self.before.count(needle),self.after.count(needle))
        for content in (CONTINUE,OBSERVER,NEXT_END):
            for forbidden in ("ipc70_bus.write","ipc70_ram.write",
                              "ctx.mmu.write","ctx.pc=0x"):
                self.assertNotIn(forbidden,content)
            self.assertNotRegex(content,r"ctx\.gpr\[[0-9]+\]\s*=(?!=)")

    def test_sixteen_original_native_runs_and_cleanup(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for token in ("derive_v221_sc_y1_ipc_leaf_harness.py",
                      "V220_SC_Y1_IPC_HANDLER verified=1",
                      "V221_SC_Y1_IPC_LEAF verified=1"):
            self.assertIn(token,script)
        example="V221_NEG_LEAF call=1 masked=1 signal=1 reply=1 stepped=1 sc=1 pc=8051905c lr=8051933c"
        self.assertIsNotNone(re.fullmatch(PASS,example))
        self.assertIsNone(re.fullmatch(PASS,example.replace("reply=1","reply=0")))
        self.assertIsNotNone(re.fullmatch(PATTERN,example.replace("masked=1","masked=0")))
        workflow=(HERE.parents[1]/".github/workflows/wii-v221-sc-y1-ipc-leaf.yml").read_text()
        for token in ("run_v221_sc_y1_ipc_leaf.sh",
                      "test_v221_sc_y1_ipc_leaf.py",
                      "V221_SC_Y1_IPC_LEAF verified=1"):
            self.assertIn(token,workflow)
        self.assertEqual(workflow.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",workflow)
        with tempfile.TemporaryDirectory() as folder:
            for name,content in (("runner",script),
                                 ("entry",(HERE/"run_v221_sc_y1_ipc_leaf.sh").read_text())):
                path=Path(folder)/name
                path.write_text(content,encoding="utf-8")
                subprocess.run(["bash","-n",str(path)],check=True)

if __name__=="__main__":
    unittest.main()
