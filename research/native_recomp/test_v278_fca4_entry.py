#!/usr/bin/env python3
"""V278 original-free bounded genuine callback entry observation tests."""
import subprocess
import unittest
from pathlib import Path
from analyze_v278_fca4_entry import parse,summarize
from derive_v278_fca4_entry_harness import (
    patch as patch_harness,GLOBAL,TRACE,RESET,FRONTIER,OBSERVER
)
from derive_v278_fca4_entry_runner import patch as patch_runner,OLD,DONE

HERE=Path(__file__).resolve().parent
END="V278_SC_CALL_WINDOW pre=1 post=1 events=2"
PRE="V278_FCA4_ENTRY n=1 phase=0 cb=1 nand=1 child=1 sc=1 guest=1 inst=100"
POST="V278_FCA4_ENTRY n=2 phase=1 cb=1 nand=1 child=0 sc=1 guest=1 inst=200"

def sample(active=True):
    lines=[]
    for _ in range(16):
        if active:lines.extend([PRE,POST,END])
        else:lines.append("V278_SC_CALL_WINDOW pre=0 post=0 events=0")
    return "\n".join(lines)

class Tests(unittest.TestCase):
    def test_16_authenticated_shape_synthetic(self):
        report=summarize(parse(sample()))
        self.assertIn("trials=16 frontier=64 stable=1 distinct=1 entries=32",report)
        self.assertIn("pre=16 post=16 child=16 sc1=32 sc3=0",report)
        self.assertIn("callback=32 nand=32",report)
        self.assertIn("entries=0 min_trial=0 max_trial=0",summarize(parse(sample(False))))

    def test_fail_closed(self):
        cases=(
            (sample().replace("n=2 phase=1","n=3 phase=1",1),"wrong_event_order"),
            (sample().replace("sc=1 guest=1","sc=256 guest=1",1),"invalid_status"),
            (sample().replace("guest=1 inst=100","guest=0 inst=100",1),"non_guest"),
            (sample().replace("guest=1 inst=200","guest=1 inst=90",1),"nonmonotonic_inst"),
            (sample().replace(END,"V278_SC_CALL_WINDOW pre=2 post=0 events=2",1),
             "invalid_event_counts"),
        )
        for data,error in cases:
            with self.subTest(error=error),self.assertRaisesRegex(ValueError,error):
                parse(data)

    def test_read_only_harness_and_seams(self):
        result=patch_harness("\n".join((GLOBAL,TRACE,RESET,FRONTIER)))
        self.assertIn(OBSERVER,result)
        self.assertIn("V278_SC_CALL_WINDOW pre=",result)
        self.assertIn("v278_entries=0u",result)
        for forbidden in ("ctx.gpr[3]=","ctx.lr=","ctx.pc =",
                          "ctx.mmu.write","ipc70_bus.write","v153_phys="):
            self.assertNotIn(forbidden,OBSERVER)
        with self.assertRaises(ValueError):
            patch_harness("not the V269 native harness")
        self.assertIn("analyze_v278_fca4_entry.py",
                      patch_runner(OLD+"\n"+DONE))
        with self.assertRaises(ValueError):
            patch_runner("unverified runner")

    def test_shell_and_private_workflow(self):
        wf=(HERE.parents[1]/
            ".github/workflows/wii-v278-fca4-entry.yml").read_text(encoding="utf-8")
        self.assertIn("V278_FCA4_ENTRY verified=1",wf)
        self.assertNotIn("upload-artifact",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        subprocess.run(["bash","-n",str(HERE/"run_v278_fca4_entry.sh")],check=True)

if __name__=="__main__":
    unittest.main()
