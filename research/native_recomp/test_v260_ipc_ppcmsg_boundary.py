#!/usr/bin/env python3
"""V260 original-free IPC PPCMSG MMIO prewrite checkpoint regressions."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v244_sc_callback_link_harness import derive as base
from derive_v259_ipc_reentry_harness import derive as previous, OBSERVER as V259
from derive_v260_ipc_ppcmsg_boundary_harness import (
    derive, WRITE_OBSERVER, CANDIDATE, V259_CONTINUE,
)
from derive_v260_ipc_ppcmsg_boundary_runner import (
    derive as runner, PATTERN, PASS, TRIAL,
)

HERE=Path(__file__).resolve().parent

class V260(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        original=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=previous(base(original))
        cls.after=derive(base(original))

    def test_prewrite_is_original_guest_only(self):
        self.assertIn(WRITE_OBSERVER,self.after)
        self.assertIn(CANDIDATE,self.after)
        self.assertIn(V259_CONTINUE,self.after)
        self.assertNotIn(V259,self.after)
        self.assertEqual(self.after.count("void HW_Reg_Write32(uint32_t addr,uint32_t value){"),1)
        self.assertEqual(self.after.count("V260_PPCMSG_BOUNDARY guest="),1)
        self.assertIn("v259_ipc_seen==1u",WRITE_OBSERVER)
        self.assertIn("v260_post_calls==64u", __import__("derive_v260_ipc_ppcmsg_boundary_harness").FRONTIER_OBSERVER)
        self.assertIn("v260_post_calls<=64u", self.after)
        self.assertIn("cpu->inst_count>v259_ipc_inst",WRITE_OBSERVER)
        self.assertIn("addr==V260Bus::IPC+V260Mail::PPCMSG",WRITE_OBSERVER)
        self.assertIn("ipc70_ram.read32(value+16u)",WRITE_OBSERVER)
        self.assertIn("ipc70_ram.valid(value,64u)",WRITE_OBSERVER)
        self.assertIn("cpu->is_running=false;throw ExceptionStop{}",WRITE_OBSERVER)
        for forbidden in ("ipc70_bus.write32(", "ipc70_ram.write", "ctx.gpr[",
                          "cpu->gpr[3]=", "cpu->pc=", "cpu->lr=",
                          "scheduler.service_one(", "v183_second_phys=value"):
            self.assertNotIn(forbidden,WRITE_OBSERVER)
        self.assertEqual(self.before.count("ipc70_bus.write32("),
                         self.after.count("ipc70_bus.write32("))
        self.assertEqual(self.before.count("ipc70_ram.write8("),
                         self.after.count("ipc70_ram.write8("))
        with self.assertRaises(ValueError):
            derive("not original-free native harness")

    def test_sixteen_original_trials_and_public_markers(self):
        s=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text(encoding="utf-8"))
        self.assertIn("derive_v260_ipc_ppcmsg_boundary_harness.py",s)
        self.assertIn("V260_SC_POSTIPC_EVENT verified=1",s)
        self.assertIn("V260_NAND_GUEST callback=1 event=1 memory=1",s)
        self.assertNotIn("V259_NAND_GUEST callback=1 reentry=1 memory=1",s)
        self.assertIsNotNone(re.fullmatch(PASS,
            "V260_PPCMSG_BOUNDARY guest=1 aligned=1 mapped=1 fresh=1 coherent=1 reply=1 open=1 mem2=1 mode_ok=0 path_phys=0 path_alias=1 idle=1 prewrite=1"))
        self.assertIsNotNone(re.fullmatch(PATTERN,
            "V260_PPCMSG_BOUNDARY guest=0 aligned=0 mapped=0 fresh=0 coherent=0 reply=1 open=0 mem2=0 mode_ok=0 path_phys=0 path_alias=0 idle=0 prewrite=1"))
        self.assertIsNotNone(re.fullmatch(TRIAL,
            "V260_NAND_GUEST callback=1 event=1 memory=1 trial=16"))
        wf=(HERE.parents[1]/".github/workflows/wii-v260-ipc-ppcmsg-boundary.yml").read_text(encoding="utf-8")
        self.assertIn("for n in $(seq 1 16); do",wf)
        self.assertIn('grep -Fqx "V260_NAND_GUEST callback=1 event=1 memory=1 trial=$n"',wf)
        self.assertIn("V260_SC_POSTIPC_EVENT verified=1",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)
        with tempfile.TemporaryDirectory() as td:
            for name,body in (("runner",s),
                ("wrapper",(HERE/"run_v260_ipc_ppcmsg_boundary.sh").read_text(encoding="utf-8"))):
                p=Path(td)/name
                p.write_text(body,encoding="utf-8")
                subprocess.run(["bash","-n",str(p)],check=True)

if __name__=="__main__":
    unittest.main()
