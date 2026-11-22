#!/usr/bin/env python3
"""V296 service ABI probes and privacy/error-classification tests."""
import unittest
from analyze_v296_native_frontier import classify
from derive_v296_service_harness import patch as patch_harness, TRACE, PROBE
from derive_v296_restored_nand_runner import patch as patch_runner, LINK, DONE

LOG=("V289_NAND_ENTRY n=1 phase=0 zero=1 sc=1 guest=1 inst=887\n"
     "V296_SERVICE_ENTRY kind=1 guest=1 direct=1 inst=900\n"
     "terminate called after throwing an instance of 'std::runtime_error'\n")

class Tests(unittest.TestCase):
    def test_early_service_guest_progress(self):
        s,ok=classify(LOG,"const char* label=\"safe\";",134)
        self.assertTrue(ok)
        self.assertIn("child=1 early=1 late=0 direct=1",s)
        self.assertIn("exception=runtime_error",s)
        self.assertIn("assertion=0000",s)

    def test_partial_reentry_and_failures(self):
        other, valid = classify(LOG.replace("kind=1","kind=2"), "public test", 134)
        self.assertTrue(valid)
        self.assertIn("early=0 late=1",other)
        self.assertFalse(classify(LOG.replace("guest=1 direct","guest=0 direct"),
                                  "not a public harness",134)[1])
        self.assertFalse(classify("", "not a public harness",0)[1])
        self.assertFalse(classify(LOG,"not a public harness",126)[1])
        with self.assertRaises(ValueError):
            classify(LOG,"not a public harness",-1)

    def test_read_only_harness_derivation(self):
        src=TRACE+"\n\"V289_NAND_ENTRY n=\";\n\"V278_FCA4_ENTRY n=\";"
        patched=patch_harness(src)
        self.assertIn("V296_SERVICE_ENTRY kind=",patched)
        self.assertIn("ctx.lr==(kind==1u?0x8052fab4u:0x8052fb10u)",patched)
        for forbidden in ("ctx.pc =","ctx.gpr[3] =","ctx.mmu.write",
                          "ctx.is_running=false"):
            self.assertNotIn(forbidden,PROBE)
        with self.assertRaises(ValueError):
            patch_harness("untrusted native harness")

    def test_bound_runner_inheritance(self):
        s=patch_runner(LINK+"\necho 'V295_BOUNDED_CANDIDATE inspected=1'")
        self.assertIn("v296-harness.o",s)
        self.assertIn("analyze_v296_native_frontier.py",s)
        self.assertIn("v295-native.log",s)
        with self.assertRaises(ValueError):
            patch_runner("untrusted runner")

if __name__=="__main__":
    unittest.main()
