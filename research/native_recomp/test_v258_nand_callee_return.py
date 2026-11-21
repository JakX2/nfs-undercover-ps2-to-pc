#!/usr/bin/env python3
"""Original-free V258 NAND successor PowerPC return regressions."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v244_sc_callback_link_harness import derive as base
from derive_v257_nand_postchild_harness import (
    derive as previous, OBSERVER as PREVIOUS_OBSERVER,
    CANDIDATE as PREVIOUS_CANDIDATE,
)
from derive_v258_nand_callee_return_harness import (
    derive, STOP, CONTINUE, RETURN_HOOK, CANDIDATE, V178_TAIL_NEXT, V178_DIAG, V178_NESTED, V178_CHECK,
)
from derive_v258_nand_callee_return_runner import (
    derive as runner, PATTERN, PASS, TRIAL,
)
HERE=Path(__file__).resolve().parent

class V258(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        src=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=previous(base(src))
        cls.after=derive(base(src))

    def test_original_guest_callee_and_return_only(self):
        self.assertIn(STOP,PREVIOUS_OBSERVER)
        self.assertNotIn(STOP,self.after)
        self.assertIn(CONTINUE,self.after)
        self.assertIn(RETURN_HOOK,self.after)
        self.assertIn(CANDIDATE,self.after)
        self.assertNotIn(PREVIOUS_CANDIDATE,self.after)
        self.assertIn(V178_TAIL_NEXT,self.after)
        self.assertIn(V178_DIAG,self.after)
        self.assertIn('V258_NAND_DEP code=',V178_DIAG)
        self.assertIn(V178_NESTED,self.after)
        self.assertIn(V178_CHECK,self.after)  # baseline V178 gate retained
        self.assertIn('addr==0x805265acu&&ctx.lr==0x8051ad64u',V178_NESTED)
        self.assertIn('addr==0x805265d4u&&ctx.lr==0x8051af08u',V178_NESTED)
        self.assertIn('ctx.inst_count>v258_callee_inst',V178_NESTED)
        self.assertIn('ctx.gpr[13]==v147_first_r13',V178_NESTED)
        self.assertIn('ctx.pc==addr',V178_NESTED)
        self.assertIn('v258_nested_guest_calls<=32u',V178_NESTED)
        self.assertIn('V258_NAND_PHASE count=',V178_NESTED)
        self.assertIn('first="<<first',V178_NESTED)
        self.assertIn('second="<<second',V178_NESTED)
        self.assertIn('v250_candidate_mode&&v257_next_seen==1u',V178_NESTED)
        self.assertIn('static unsigned v258_return_seen=0u,v258_nested_guest_calls=0u',self.after)
        self.assertIn('nwii::runtime::v258_return_seen=nwii::runtime::v258_nested_guest_calls=0u',self.after)
        self.assertIn("addr==0x8051ad3cu&&ctx.lr==0x804f0f68u",CONTINUE)
        self.assertIn("ctx.pc==0x804f0f68u",RETURN_HOOK)
        self.assertIn("v258_callee_inst=ctx.inst_count",CONTINUE)
        self.assertIn("ctx.inst_count>v258_callee_inst",RETURN_HOOK)
        self.assertIn("V258_NAND_CALLEE_RETURN guest=",RETURN_HOOK)
        self.assertIn("V258_NAND_GUEST callback=",CANDIDATE)
        with self.assertRaises(ValueError):
            derive("unmatched original-free source")

    def test_no_original_cpu_or_ios_mutation(self):
        parts=CONTINUE+RETURN_HOOK+CANDIDATE+V178_DIAG+V178_NESTED
        for forbidden in ("ipc70_bus.write","ipc70_ram.write","ctx.mmu.write",
                          "c.mmu.write","ctx.gpr[3]=","scheduler.service_one("):
            self.assertNotIn(forbidden,parts)
        self.assertIsNone(re.search(r"\bctx\.(?:pc|lr)\s*=(?!=)",parts))
        for original in ("ipc70_bus.tick(","ipc70_ram.write8(","ctx.mmu.write32("):
            self.assertEqual(self.before.count(original),self.after.count(original))

    def test_owner_trial_runner_guards(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text(encoding="utf-8"))
        for token in ("derive_v258_nand_callee_return_harness.py",
                      "V256_SC_NAND_CHILD_RETURN verified=1",
                      "V257_SC_NAND_POSTCHILD verified=1",
                      "V258_SC_NAND_CALLEE_RETURN verified=1",
                      '"$work/private-v248.dol" owner-callback "$owner"'):
            self.assertIn(token,script)
        self.assertNotIn("V257_NAND_GUEST callback=1 next=1 memory=1",script)
        self.assertEqual(script.count('test "$(grep -Ec \x27^V258_NAND_GUEST'),4)
        self.assertIn('test "$(grep -Ec \x27^V254_NAND_CHILD',script)
        row="V258_NAND_CALLEE_RETURN guest=1 mapped=1 reply=0 pending=0 coherent=1 sc=1"
        self.assertIsNotNone(re.fullmatch(PASS,row))
        self.assertIsNotNone(re.fullmatch(PATTERN,row.replace("guest=1","guest=0")))
        self.assertIsNone(re.fullmatch(PASS,row.replace("coherent=1","coherent=0")))
        self.assertIsNotNone(re.fullmatch(TRIAL,"V258_NAND_GUEST callback=1 returned=1 memory=1 trial=16"))
        wf=(HERE.parents[1]/".github/workflows/wii-v258-nand-callee-return.yml").read_text()
        for expected in ("run_v258_nand_callee_return.sh","test_v258_nand_callee_return.py",
                         "V258_SC_NAND_CALLEE_RETURN verified=1",
                         "V257_SC_NAND_POSTCHILD verified=1"):
            self.assertIn(expected,wf)
        self.assertNotIn("          grep -E '^V257_NAND_GUEST callback=1 next=1 memory=1",wf)
        self.assertIn("V258_NAND_DEP code=",wf)
        self.assertIn("V258_NAND_PHASE count=",wf)
        self.assertIn("V258_NAND_PHASE count=",script)
        self.assertNotIn("upload-artifact",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        with tempfile.TemporaryDirectory() as td:
            for name,body in (("runner",script),
                ("wrapper",(HERE/"run_v258_nand_callee_return.sh").read_text(encoding="utf-8"))):
                file=Path(td)/name
                file.write_text(body,encoding="utf-8")
                subprocess.run(["bash","-n",str(file)],check=True)

if __name__=="__main__":
    unittest.main()
