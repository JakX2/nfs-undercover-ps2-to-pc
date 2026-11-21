#!/usr/bin/env python3
"""Original-free V256 owner-native NAND child PPC return regression."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v244_sc_callback_link_harness import derive as base
from derive_v254_nand_first_child_harness import derive as previous, OBSERVER as PREVIOUS_OBSERVER, CANDIDATE as PREVIOUS_CANDIDATE
from derive_v256_nand_child_return_harness import derive, STOP, CONTINUE, CALLBACK, V178_CHILD, CANDIDATE
from derive_v256_nand_child_return_runner import derive as runner, PATTERN, PASS, TRIAL
HERE=Path(__file__).resolve().parent

class V256(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        src=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=previous(base(src))
        cls.after=derive(base(src))

    def test_executes_original_child_and_return_without_patching(self):
        self.assertIn(STOP,PREVIOUS_OBSERVER)
        self.assertNotIn(STOP,self.after)
        self.assertIn(CONTINUE,self.after)
        self.assertIn(CALLBACK,self.after)
        self.assertIn(V178_CHILD,self.after)
        self.assertIn(CANDIDATE,self.after)
        self.assertNotIn(PREVIOUS_CANDIDATE,self.after)
        self.assertIn("addr==0x8052fa60u&&ctx.lr==0x8051e0b8u",CONTINUE)
        self.assertIn("ctx.pc==0x8051e0b8u",CALLBACK)
        self.assertIn("v256_child_inst=ctx.inst_count",CONTINUE)
        self.assertIn("ctx.inst_count>v256_child_inst",CALLBACK)
        self.assertIn("V256_NAND_RETURN child=",CALLBACK)
        self.assertIn("V256_NAND_GUEST callback=",CANDIDATE)
        self.assertIn("owner-callback only; owner baseline V163 remains",CANDIDATE)
        with self.assertRaises(ValueError):derive("unmatched base")

    def test_no_synthetic_guest_execution(self):
        for string in ("ipc70_bus.tick(","scheduler.service_one(",
                       "ipc70_bus.write32(","ipc70_ram.write8(",
                       "ctx.mmu.write32("):
            self.assertEqual(self.before.count(string),self.after.count(string))
        for part in (CONTINUE,CALLBACK,V178_CHILD,CANDIDATE):
            for mutation in ("ipc70_bus.write","ipc70_ram.write",
                             "ctx.mmu.write","c.mmu.write",
                             "ctx.gpr[3]=","ctx.pc=0x"):
                self.assertNotIn(mutation,part)

    def test_runner_16_owner_trials_and_private_cleanup(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text(encoding="utf-8"))
        for marker in ("derive_v256_nand_child_return_harness.py",
                       "V254_SC_NAND_FIRST_CHILD verified=1",
                       "V256_SC_NAND_CHILD_RETURN verified=1",
                       '"$work/private-v248.dol" owner-callback "$owner"',
                       'for n in $(seq 1 16); do'):
            self.assertIn(marker,script)
        good="V256_NAND_RETURN child=1 guest=1 frame=1 reply=1 mapped=1 pending=1 coherent=1 sc=1"
        self.assertIsNotNone(re.fullmatch(PASS,good))
        self.assertIsNotNone(re.fullmatch(PATTERN,good.replace("guest=1","guest=0")))
        self.assertIsNone(re.fullmatch(PASS,good.replace("child=1","child=0")))
        self.assertIsNotNone(re.fullmatch(TRIAL,"V256_NAND_GUEST callback=1 returned=1 memory=1 trial=16"))
        wf=(HERE.parents[1]/".github/workflows/wii-v256-nand-child-return.yml").read_text()
        for marker in ("run_v256_nand_child_return.sh","test_v256_nand_child_return.py",
                       "V256_SC_NAND_CHILD_RETURN verified=1"):
            self.assertIn(marker,wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)
        with tempfile.TemporaryDirectory() as td:
            for filename,source in (("runner",script),("wrapper",(HERE/"run_v256_nand_child_return.sh").read_text(encoding="utf-8"))):
                path=Path(td)/filename;path.write_text(source,encoding="utf-8")
                subprocess.run(["bash","-n",str(path)],check=True)

if __name__=="__main__":
    unittest.main()
