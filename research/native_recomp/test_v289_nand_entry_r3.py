#!/usr/bin/env python3
"""V289 original-free NAND r3 service-entry and privacy regressions."""
import subprocess
import unittest
from pathlib import Path
from analyze_v289_nand_entry_r3 import parse,summary
from derive_v289_nand_entry_r3_harness import (
    patch as patch_harness,GLOBAL,TRACE,RESET,FRONTIER,OBSERVER
)
from derive_v289_nand_entry_r3_runner import (
    patch as patch_runner,OLD,DONE
)

HERE=Path(__file__).resolve().parent
P="V289_NAND_ENTRY n=1 phase=0 zero=1 sc=1 guest=1 inst=123"
Q="V289_NAND_ENTRY n=2 phase=1 zero=0 sc=1 guest=1 inst=223"
END="V289_NAND_WINDOW pre=1 post=1 zero=1 entries=2"

def fixture(with_entries=True):
    lines=[]
    for _ in range(16):
        if with_entries:lines.extend((P,Q,END))
        else:lines.append("V289_NAND_WINDOW pre=0 post=0 zero=0 entries=0")
    return "\n".join(lines)

class Tests(unittest.TestCase):
    def test_bounded_16_trial_service_counts(self):
        report=summary(parse(fixture()))
        self.assertIn("trials=16 frontier=64 stable=1 distinct=1 entries=32",report)
        self.assertIn("pre=16 post=16 zero=16 sc1=32 sc3=0",report)
        self.assertIn("entries=0 min_trial=0 max_trial=0",
                      summary(parse(fixture(False))))

    def test_malformed_inputs_fail_closed(self):
        cases=(
            (fixture().replace("n=2 phase=1","n=3 phase=1",1),"seq"),
            (fixture().replace("sc=1 guest=1","sc=257 guest=1",1),"status"),
            (fixture().replace("guest=1 inst=123","guest=0 inst=123",1),"guest"),
            (fixture().replace("guest=1 inst=223","guest=1 inst=100",1),"inst_order"),
            (fixture().replace(END,"V289_NAND_WINDOW pre=0 post=2 zero=1 entries=2",1),
             "inconsistent_window"),
        )
        for altered,error in cases:
            with self.subTest(error=error),self.assertRaisesRegex(ValueError,error):
                parse(altered)

    def test_read_only_derivation_and_regression_anchors(self):
        out=patch_harness("\n".join((GLOBAL,TRACE,RESET,FRONTIER)))
        self.assertIn(OBSERVER,out)
        self.assertIn("V289_NAND_WINDOW pre=",out)
        for illegal in ("ctx.gpr[3] =", "ctx.pc =", "ctx.mmu.write",
                        "ipc70_bus.write", "ipc70_ram.write",
                        "ctx.is_running=false"):
            self.assertNotIn(illegal,OBSERVER)
        with self.assertRaises(ValueError):
            patch_harness("untrusted non-V278 native source")
        self.assertIn("analyze_v289_nand_entry_r3.py",patch_runner(OLD+"\n"+DONE))
        with self.assertRaises(ValueError):
            patch_runner("not the authenticated V278 runner")

    def test_bash_workflow_private_boundaries(self):
        wf=(HERE.parents[1]/
            ".github/workflows/wii-v289-nand-early-service.yml").read_text(
                encoding="utf-8")
        self.assertIn("V289_NAND_ENTRY verified=1",wf)
        self.assertNotIn("upload-artifact",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        subprocess.run(["bash","-n",str(HERE/"run_v289_nand_entry_r3.sh")],check=True)

if __name__=="__main__":
    unittest.main()
