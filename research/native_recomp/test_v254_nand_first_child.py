#!/usr/bin/env python3
"""V254 original-free native NAND function first real child-call tests."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v244_sc_callback_link_harness import derive as base
from derive_v254_nand_first_child_harness import (
    derive, V178_CALLEE, V178_SCOPED, NAND_RESUME,
    OBSERVER, VERIFY,
)
from derive_v254_nand_first_child_runner import derive as runner, PATTERN, PASS, TRIAL
HERE=Path(__file__).resolve().parent

class V254(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        src=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=base(src)
        cls.after=derive(cls.before)

    def test_original_nand_enters_native_child_without_forcing_return(self):
        self.assertIn("V254_NAND_CHILD guest=",self.after)
        self.assertIn("V178 owner-original SC reply callee differs from V177 proof",self.after)
        self.assertIn(V178_SCOPED,self.after)
        self.assertIn("if(v250_candidate_mode&&v252_nand_entry_seen==1u",V178_SCOPED)
        self.assertIn("addr==0x8051e06cu&&ctx.lr==0x804f0f54u",V178_SCOPED)
        self.assertIn("v254_nand_inst=ctx.inst_count",NAND_RESUME)
        self.assertIn("ctx.inst_count>v254_nand_inst",OBSERVER)
        self.assertIn("v254_next_pc=addr;v254_next_lr=ctx.lr",OBSERVER)
        self.assertIn("V254_NAND_GUEST callback=",VERIFY)
        self.assertIn("continue; // only the independent owner-callback mode",VERIFY)
        self.assertIn("ctx.is_running=false;throw ExceptionStop{};",OBSERVER)
        self.assertNotIn("ctx.is_running=false;throw ExceptionStop{};",NAND_RESUME)
        with self.assertRaises(ValueError):derive("unmatched")

    def test_preserve_baseline_and_no_original_guest_mutation(self):
        self.assertEqual(self.before.count('V244 original callback nested link provenance missing'),
                         self.after.count('V244 original callback nested link provenance missing'))
        for segment in (NAND_RESUME,OBSERVER,VERIFY,V178_SCOPED):
            for forbidden in ("ipc70_bus.write","ipc70_ram.write","ctx.mmu.write",
                              "c.mmu.write","ctx.gpr[3]=","ctx.pc=0x"):
                self.assertNotIn(forbidden,segment)
        self.assertIn("if(v250_probe){",VERIFY)
        self.assertIn('check(addr==0x80545100u&&ctx.lr==0x804f1e40u,',V178_SCOPED)

    def test_owner_sixteen_randomized_trials_and_cleanup(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text(encoding="utf-8"))
        for item in ("derive_v254_nand_first_child_harness.py",
                     "V249_SC_AUTH_CALLBACK_LINK verified=1",
                     "V250_SC_NAND_BCTRL verified=1",
                     "V254_SC_NAND_FIRST_CHILD verified=1",
                     '"$work/private-v248.dol" owner-callback "$owner"',
                     'for n in $(seq 1 16); do'):
            self.assertIn(item,script)
        row="V254_NAND_CHILD guest=1 caller=1 reply=1 mapped=1 frame=1 coherent=1 text=1 low=0 sc=1 pc=805265ac lr=8051e08c"
        self.assertIsNotNone(re.fullmatch(PASS,row))
        self.assertIsNotNone(re.fullmatch(PATTERN,row.replace("guest=1","guest=0")))
        self.assertIsNotNone(re.fullmatch(TRIAL,
            "V254_NAND_GUEST callback=1 next=1 memory=1 trial=16"))
        self.assertIsNone(re.fullmatch(PASS,row.replace("caller=1","caller=0")))
        wf=(HERE.parents[1]/".github/workflows/wii-v254-nand-first-child.yml").read_text()
        for item in ("run_v254_nand_first_child.sh","test_v254_nand_first_child.py",
                     "V254_SC_NAND_FIRST_CHILD verified=1"):
            self.assertIn(item,wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)
        with tempfile.TemporaryDirectory() as tmp:
            for name,content in (("runner",script),("wrapper",(HERE/"run_v254_nand_first_child.sh").read_text(encoding="utf-8"))):
                path=Path(tmp)/name;path.write_text(content,encoding="utf-8")
                subprocess.run(["bash","-n",str(path)],check=True)

if __name__=="__main__":
    unittest.main()
