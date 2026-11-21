#!/usr/bin/env python3
"""Original-free V257 NAND postchild PowerPC continuation regressions."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v244_sc_callback_link_harness import derive as base
from derive_v256_nand_child_return_harness import (
    derive as previous, CALLBACK as PREVIOUS_CALLBACK,
    CANDIDATE as PREVIOUS_CANDIDATE,
)
from derive_v257_nand_postchild_harness import (
    derive, STOP, CONTINUE, OBSERVER, CANDIDATE,
)
from derive_v257_nand_postchild_runner import (
    derive as runner, PATTERN, PASS, TRIAL,
)

HERE=Path(__file__).resolve().parent

class V257(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        src=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=previous(base(src))
        cls.after=derive(base(src))

    def test_resume_real_ppc_after_verified_return(self):
        self.assertIn(STOP,PREVIOUS_CALLBACK)
        self.assertNotIn(STOP,self.after)
        self.assertIn(CONTINUE,self.after)
        self.assertIn(OBSERVER,self.after)
        self.assertIn(CANDIDATE,self.after)
        self.assertNotIn(PREVIOUS_CANDIDATE,self.after)
        self.assertIn("v256_return_seen==1u",OBSERVER)
        self.assertIn("ctx.inst_count>v257_return_inst",OBSERVER)
        self.assertIn("v257_return_inst=ctx.inst_count",CONTINUE)
        self.assertIn("return false;",CONTINUE)
        self.assertIn("V257_NAND_NEXT guest=",OBSERVER)
        self.assertIn("V257_NAND_GUEST callback=",CANDIDATE)
        self.assertIn("v256_return_seen==1u",CANDIDATE)
        with self.assertRaises(ValueError):
            derive("unmatched public base")

    def test_no_guest_state_rewrites_or_native_reply_fabrication(self):
        for forbidden in ("ipc70_bus.write","ipc70_ram.write",
                          "ctx.mmu.write","c.mmu.write",
                          "ctx.gpr[3]=", "ctx.pc=", "ctx.lr=",
                          "scheduler.service_one("):
            self.assertNotIn(forbidden,CONTINUE+OBSERVER+CANDIDATE)
        for existing in ("ipc70_bus.tick(","ipc70_ram.write8(","ctx.mmu.write32("):
            self.assertEqual(self.before.count(existing),self.after.count(existing))

    def test_runner_owner_trials_and_source_guards(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text(encoding="utf-8"))
        for name in ("derive_v257_nand_postchild_harness.py",
                     "V256_SC_NAND_CHILD_RETURN verified=1",
                     "V257_SC_NAND_POSTCHILD verified=1",
                     '"$work/private-v248.dol" owner-callback "$owner"'):
            self.assertIn(name,script)
        self.assertNotIn("V256_NAND_GUEST callback=1 returned=1 memory=1",script)
        self.assertEqual(script.count('test "$(grep -Ec \x27^V257_NAND_GUEST'),3)
        self.assertIn('test "$(grep -Ec \x27^V254_NAND_CHILD',script)
        row="V257_NAND_NEXT guest=1 caller=1 code=1 mapped=1 reply=0 coherent=1 sc=1 pc=80545100 lr=8051e0d0"
        self.assertIsNotNone(re.fullmatch(PASS,row))
        self.assertIsNotNone(re.fullmatch(PATTERN,row.replace("guest=1","guest=0")))
        self.assertIsNone(re.fullmatch(PASS,row.replace("caller=1","caller=0")))
        self.assertIsNotNone(re.fullmatch(TRIAL,"V257_NAND_GUEST callback=1 next=1 memory=1 trial=16"))
        wf=(HERE.parents[1]/".github/workflows/wii-v257-nand-postchild.yml").read_text(encoding="utf-8")
        for expected in ("run_v257_nand_postchild.sh", "test_v257_nand_postchild.py",
                         "V256_SC_NAND_CHILD_RETURN verified=1",
                         "V257_SC_NAND_POSTCHILD verified=1", "V257_LOG_COUNTS next="):
            self.assertIn(expected,wf)
        self.assertNotIn("          grep -E '^V256_NAND_GUEST callback=1 returned=1 memory=1",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)
        with tempfile.TemporaryDirectory() as td:
            for filename,source in (("runner",script),
                    ("wrapper",(HERE/"run_v257_nand_postchild.sh").read_text(encoding="utf-8"))):
                path=Path(td)/filename
                path.write_text(source,encoding="utf-8")
                subprocess.run(["bash","-n",str(path)],check=True)

if __name__=="__main__":
    unittest.main()
