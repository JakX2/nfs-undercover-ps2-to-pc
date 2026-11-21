#!/usr/bin/env python3
"""Original-free V215 second IOS negative Y1 vector bridge tests."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v212_sc_y2_rfi_harness import derive as previous, OBSERVER as PREVIOUS_OBSERVER, NEXT_END as PREVIOUS_END
from derive_v215_sc_y1_negative_vector_harness import derive, STOP, CONTINUE, NEXT_END
from derive_v215_sc_y1_negative_vector_runner import derive as runner, PATTERN, PASS
HERE=Path(__file__).resolve().parent

class V215(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=previous(source)
        cls.after=derive(source)

    def test_authentic_guest_rfi_to_native_covered_irq(self):
        self.assertIn(STOP,PREVIOUS_OBSERVER)
        self.assertNotIn(STOP,self.after)
        self.assertIn(CONTINUE,self.after)
        self.assertIn(NEXT_END,self.after)
        self.assertNotIn(PREVIOUS_END,self.after)
        for token in ("v215_scheduler.service_one(ctx.msr)",
                      "int32_t(ipc70_ram.read32(v183_second_phys+4u))==V215IOS::Invalid",
                      "undercover::wii::enter_external_irq(",
                      "irq74_vector,true",
                      "ctx.srr0==original_pc",
                      "ctx.srr1==(original_msr&undercover::wii::ExternalSrr1Mask)",
                      "ctx.gpr==original_gprs",
                      "++v215_vector_seen",
                      "V215_Y1_VECTOR"):
            self.assertIn(token,CONTINUE)
        self.assertIn("v215_vector_seen==1u",NEXT_END)
        with self.assertRaises(ValueError):derive("unmatched base")

    def test_no_synthetic_success_or_guest_mutation(self):
        for token in ("ipc70_bus.tick(","ctx.mmu.write32(",
                      "ipc70_ram.write8(","ipc70_bus.write32("):
            self.assertEqual(self.before.count(token),self.after.count(token))
        for chunk in (CONTINUE,NEXT_END):
            for forbidden in ("ipc70_bus.write","ipc70_ram.write",
                              "ctx.mmu.write","ctx.gpr[3]=",
                              "ctx.pc=0x80000500","ctx.msr=0x"):
                self.assertNotIn(forbidden,chunk)
        self.assertIn("V215IOS::Invalid",CONTINUE)
        self.assertNotIn("V215IOS::File",CONTINUE)

    def test_owner_16_trial_and_private_cleanup(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for marker in ("derive_v215_sc_y1_negative_vector_harness.py",
                       "V212_SC_Y2_RFI verified=1",
                       "V215_SC_Y1_NEGATIVE_VECTOR verified=1"):
            self.assertIn(marker,script)
        good="V215_Y1_VECTOR pump=1 published=1 signal=1 empty=1 cpu=1 entered=1 saved=1 regs=1 masked=1 sc=1"
        self.assertIsNotNone(re.fullmatch(PASS,good))
        self.assertIsNotNone(re.fullmatch(PATTERN,good.replace("signal=1","signal=0")))
        self.assertIsNone(re.fullmatch(PASS,good.replace("entered=1","entered=0")))
        from diagnose_v215_compile_failure import diagnose as diag
        compiler="harness.cpp:7798:12: error: 'v215_ctrl' was not declared in this scope"
        self.assertEqual(diag(compiler, "\n"*7797+"v215_ctrl;", "harness"),
            "V215_COMPILE_DIAG unit=harness kind=undeclared line=7798 symbol=other at_code=1 cls=ipc")
        self.assertIn("diagnose_v215_compile_failure.py",script)
        wf=(HERE.parents[1]/".github/workflows/wii-v215-sc-y1-negative-vector.yml").read_text()
        for m in ("run_v215_sc_y1_negative_vector.sh",
                  "test_v215_sc_y1_negative_vector.py",
                  "V215_SC_Y1_NEGATIVE_VECTOR verified=1"):
            self.assertIn(m,wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)
        with tempfile.TemporaryDirectory() as temp:
            for name,content in (("runner",script),("wrapper",(HERE/"run_v215_sc_y1_negative_vector.sh").read_text())):
                p=Path(temp)/name;p.write_text(content,encoding="utf-8")
                subprocess.run(["bash","-n",str(p)],check=True)

if __name__=="__main__":
    unittest.main()
