#!/usr/bin/env python3
"""Source-only V259 authentic PowerPC IPC reentry observer regressions."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v244_sc_callback_link_harness import derive as base
from derive_v258_nand_callee_return_harness import derive as previous, CANDIDATE as PREVIOUS_CANDIDATE
from derive_v259_ipc_reentry_harness import derive, OBSERVER, CANDIDATE
from derive_v259_ipc_reentry_runner import derive as runner, PATTERN, PASS, TRIAL

HERE=Path(__file__).resolve().parent

class V259(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        original=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=previous(base(original))
        cls.after=derive(base(original))

    def test_exact_authentic_ipc_reentry_without_guest_mutation(self):
        self.assertIn(OBSERVER,self.after)
        self.assertIn(CANDIDATE,self.after)
        self.assertNotIn(PREVIOUS_CANDIDATE,self.after)
        self.assertIn("addr==0x8051906cu&&ctx.lr==0x805192ecu",OBSERVER)
        self.assertIn("ctx.inst_count>v258_callee_inst",OBSERVER)
        self.assertIn("v250_candidate_mode&&v257_next_seen==1u",OBSERVER)
        self.assertIn("V259_IPC_REENTRY guest=",OBSERVER)
        self.assertIn("V259_NAND_GUEST callback=",CANDIDATE)
        self.assertIn("ctx.pc==addr",OBSERVER)
        self.assertNotIn("ctx.pc=0x",OBSERVER)
        for source in (OBSERVER,CANDIDATE):
            for forbidden in ("ipc70_bus.write","ipc70_ram.write","ctx.mmu.write",
                              "c.mmu.write","ctx.gpr[3]=","scheduler.service_one("):
                self.assertNotIn(forbidden,source)
        self.assertIsNone(re.search(r"\bctx\.(?:pc|lr)\s*=(?!=)",OBSERVER+CANDIDATE))
        for name in ("ipc70_bus.tick(","ipc70_ram.write8(","ctx.mmu.write32("):
            self.assertEqual(self.before.count(name),self.after.count(name))
        with self.assertRaises(ValueError):
            derive("not original-free native harness")

    def test_runner_guard_16_original_trials(self):
        s=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text(encoding="utf-8"))
        for field in ("derive_v259_ipc_reentry_harness.py",
                      "V257_SC_NAND_POSTCHILD verified=1",
                      "V259_SC_IPC_REENTRY verified=1",
                      "V259_NAND_GUEST callback=1 reentry=1 memory=1"):
            self.assertIn(field,s)
        self.assertNotIn("V257_NAND_GUEST callback=1 next=1 memory=1",s)
        self.assertEqual(s.count('test "$(grep -Ec \x27^V259_NAND_GUEST'),4)
        self.assertIsNotNone(re.fullmatch(PASS,
            "V259_IPC_REENTRY guest=1 caller=1 mapped=1 coherent=1 reply=0 second=1 sc=1 pc=8051906c lr=805192ec"))
        self.assertIsNotNone(re.fullmatch(PATTERN,
            "V259_IPC_REENTRY guest=0 caller=1 mapped=1 coherent=1 reply=1 second=1 sc=1 pc=8051906c lr=805192ec"))
        self.assertIsNotNone(re.fullmatch(TRIAL,
            "V259_NAND_GUEST callback=1 reentry=1 memory=1 trial=16"))
        with tempfile.TemporaryDirectory() as td:
            for name,body in (("runner",s),
                ("wrapper",(HERE/"run_v259_ipc_reentry.sh").read_text(encoding="utf-8"))):
                path=Path(td)/name;path.write_text(body,encoding="utf-8")
                subprocess.run(["bash","-n",str(path)],check=True)

if __name__=="__main__":
    unittest.main()
