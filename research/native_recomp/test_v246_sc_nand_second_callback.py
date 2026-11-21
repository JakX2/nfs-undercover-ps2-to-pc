#!/usr/bin/env python3
"""Original-free V246 nested NAND callback and PPC CTR audit."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v244_sc_callback_link_harness import derive as previous, TRACE as PARENT_TRACE
from derive_v246_sc_nand_second_callback_harness import derive, PROBE, SEND
from derive_v246_sc_nand_second_callback_runner import derive as runner, TARGET, CTR
HERE=Path(__file__).resolve().parent

class V246(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=previous(source)
        cls.after=derive(source)

    def test_authentic_callback_and_prologue_anchors(self):
        self.assertIn(PARENT_TRACE+PROBE,self.after)
        self.assertIn(SEND,self.after)
        self.assertIn("v246_user_seen==1u&&v246_save_seen==1u",self.after)
        for item in ("v244_cb_seen==1u","v244_save_seen==1u",
                     "v246_outer+260u","v246_nested+4u",
                     "addr==0x804f0e04u","addr==0x80545100u",
                     "ctx.ctr==v246_user_callback",
                     "V246_SECOND_TARGET","V246_SECOND_CTR"):
            self.assertIn(item,PROBE)
        with self.assertRaises(ValueError):derive("unmatched fixture")

    def test_read_only_and_private_output(self):
        for item in ("ipc70_bus.write32(","ipc70_ram.write8(",
                     "ctx.mmu.write32(","scheduler.service_one("):
            self.assertEqual(self.before.count(item),self.after.count(item))
        for body in (PROBE,SEND):
            for forbidden in ("ipc70_bus.write","ipc70_ram.write",
                              "ctx.mmu.write","<<ctx.ctr","<<ctx.gpr",
                              "<<v246_outer","<<v246_nested","<<v246_user_callback"):
                self.assertNotIn(forbidden,body)
            self.assertNotRegex(body,r"ctx\.gpr\[[0-9]+\]\s*=(?!=)")

    def test_sixteen_owner_trials_and_cleanup(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for marker in ("derive_v246_sc_nand_second_callback_harness.py",
                       "V244_SC_CALLBACK_LINK verified=1",
                       "V246_SC_NAND_SECOND_CALLBACK verified=1"):
            self.assertIn(marker,script)
        self.assertIsNotNone(re.fullmatch(
            TARGET,"V246_SECOND_TARGET outer=1 nested=1 text=1 isfs=0 nand=0 cb=0 null=0"))
        self.assertIsNotNone(re.fullmatch(
            CTR,"V246_SECOND_CTR known=1 match=0 isfs=0 nand=1 cb=0 text=1 outer_lr=1"))
        wf=(HERE.parents[1]/".github/workflows/wii-v246-sc-nand-second-callback.yml").read_text()
        for marker in ("run_v246_sc_nand_second_callback.sh",
                       "test_v246_sc_nand_second_callback.py",
                       "V246_SC_NAND_SECOND_CALLBACK verified=1"):
            self.assertIn(marker,wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)
        with tempfile.TemporaryDirectory() as temp:
            for name,script_body in (("runner.sh",script),
                    ("entry.sh",(HERE/"run_v246_sc_nand_second_callback.sh").read_text())):
                path=Path(temp)/name
                path.write_text(script_body,encoding="utf-8")
                subprocess.run(["bash","-n",str(path)],check=True)

if __name__=="__main__":
    unittest.main()
