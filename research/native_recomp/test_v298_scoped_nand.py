#!/usr/bin/env python3
"""V298 original-free phase scope, privacy and regression guards."""
import unittest
from derive_v298_scope_reply_observer import OLD,NEW,CHECK,patch as scope
from derive_v298_scoped_nand_runner import LINK,DONE,patch as runner
from analyze_v298_scope_native import inspect

SOURCE=OLD+"\n"+CHECK+"\nV296_SERVICE_ENTRY kind=\nv250_nand_seen\n"
LOG=("V289_NAND_ENTRY n=1 phase=0 zero=1 sc=1 guest=1 inst=100\n"
     "V296_SERVICE_ENTRY kind=1 guest=1 direct=1 inst=121\n")

class Tests(unittest.TestCase):
    def test_guard_scoped_only_after_verified_callback(self):
        s=scope(SOURCE)
        self.assertIn(NEW,s)
        self.assertIn(CHECK,s)
        self.assertNotIn("ctx.gpr[3] =",s)
        self.assertNotIn("ctx.mmu.write",s)
        with self.assertRaises(ValueError):
            scope("untrusted harness")

    def test_native_outcome_rejects_old_assertion(self):
        summary,ok=inspect(LOG,"a public check",134)
        self.assertTrue(ok)
        self.assertIn("child=1 early=1 late=0 writer=0 old_assert=0",summary)
        old=LOG+"what(): "+CHECK+"\n"
        self.assertFalse(inspect(old,"a public check",134)[1])
        self.assertFalse(inspect("", "a public check",0)[1])

    def test_runner_keeps_generated_aot_intact(self):
        r=runner(LINK+"\n"+DONE)
        self.assertIn("v298-harness.o",r)
        self.assertIn("analyze_v298_scope_native.py",r)
        self.assertIn("v294-generated.o",r)
        with self.assertRaises(ValueError):
            runner("unknown native candidate")

if __name__=="__main__":
    unittest.main()
