#!/usr/bin/env python3
"""V298 original-free phase scope, privacy and regression guards."""
import unittest
from derive_v298_scope_reply_observer import (OLD,NEW,CHECK,SUBMIT_OLD,SUBMIT_NEW,
                                                CLIENT_OLD,CLIENT_NEW,IOS_OPEN_OLD,IOS_OPEN_NEW,
                                                IOS_OPEN_EXPLICIT,summarize_seams,patch as scope)
from derive_v298_scoped_nand_runner import LINK,DONE,patch as runner
from analyze_v298_scope_native import inspect

SOURCE=(OLD+"\n"+SUBMIT_OLD+"\n"+CLIENT_OLD+"\n"+IOS_OPEN_OLD+
        "\n"+IOS_OPEN_EXPLICIT+"\n"+CHECK+
        "\nV296_SERVICE_ENTRY kind=\nv250_nand_seen\n")
LOG=("V289_NAND_ENTRY n=1 phase=0 zero=1 sc=1 guest=1 inst=100\n"
     "V296_SERVICE_ENTRY kind=1 guest=1 direct=1 inst=121\n")

class Tests(unittest.TestCase):
    def test_guard_scoped_only_after_verified_callback(self):
        s=scope(SOURCE)
        self.assertIn(NEW,s)
        self.assertIn(SUBMIT_NEW,s)
        self.assertIn(CLIENT_NEW,s)
        self.assertIn(IOS_OPEN_NEW,s)
        self.assertIn(IOS_OPEN_EXPLICIT,s)
        self.assertNotIn(IOS_OPEN_OLD,s)
        self.assertNotIn(CLIENT_OLD,s)
        self.assertIn("||addr==0x805194c4u)",CLIENT_NEW)
        self.assertEqual(s.count("ipc69_entry(addr,ctx);return;"),1)
        self.assertIn(CHECK,s)
        self.assertNotIn("ctx.gpr[3] =",s)
        self.assertNotIn("ctx.mmu.write",s)
        with self.assertRaises(ValueError):
            scope("untrusted harness")

    def test_v313_sanitized_source_anchor_classifier(self):
        good=summarize_seams(SOURCE)
        self.assertIn("reply=1 submit=1 client=1 ios=1 explicit=1",good)
        self.assertIn("check=1 service=1 nand=1",good)
        missing=summarize_seams(SOURCE.replace(IOS_OPEN_OLD,"",1))
        self.assertIn("ios=0",missing)
        doubled=summarize_seams(SOURCE+"\n"+IOS_OPEN_EXPLICIT)
        self.assertIn("explicit=2",doubled)
        self.assertNotIn("ctx.gpr",good)

    def test_v311_ios_open_observer_phase_isolation(self):
        # Historical V71 instrumentation is active until the verified
        # NAND callback, while the real IOS_Open entry always remains.
        cases=[
            (False,False,False,False),
            (False,True,True,False),
            (True,False,False,True),
            (True,False,True,True),
            (True,True,False,True),
            (True,True,True,False),
        ]
        self.assertEqual(
            IOS_OPEN_NEW,
            "    if(!stm70_open||"
            "(v250_candidate_mode&&v250_nand_seen==1u))return false;"
        )
        for open_active,candidate,nand_seen,expected in cases:
            observed=open_active and not(candidate and nand_seen)
            self.assertEqual(observed,expected)
        with self.assertRaises(ValueError):
            scope(SOURCE.replace(IOS_OPEN_OLD,"",1))
        with self.assertRaises(ValueError):
            scope(SOURCE+"\n"+IOS_OPEN_OLD)
        with self.assertRaises(ValueError):
            scope(SOURCE.replace(IOS_OPEN_EXPLICIT,"",1))

    def test_client_observer_phase_truth_table(self):
        # Broad IPC client observer is allowed in baseline and before
        # authentic V250 callback; explicit client entry is never masked.
        for candidate in (False,True):
            for nand_seen in (False,True):
                for v177_seen in (False,True):
                    for explicit in (False,True):
                        active=True
                        observed=(active and not v177_seen and
                                  (not candidate or not nand_seen)) or explicit
                        if explicit:
                            self.assertTrue(observed)
                        elif candidate and nand_seen:
                            self.assertFalse(observed)
                        elif v177_seen:
                            self.assertFalse(observed)
                        else:
                            self.assertTrue(observed)

    def test_missing_or_duplicate_client_seam_fails_closed(self):
        for corrupted in (
            SOURCE.replace(CLIENT_OLD,"",1),
            SOURCE+"\n"+CLIENT_OLD,
        ):
            with self.assertRaises(ValueError):
                scope(corrupted)

    def test_native_outcome_rejects_old_assertion(self):
        summary,ok=inspect(LOG,"a public check",134)
        self.assertTrue(ok)
        self.assertIn("child=1 early=1 late=0 writer=0 old_assert=0",summary)
        old=LOG+"what(): "+CHECK+"\n"
        self.assertFalse(inspect(old,"a public check",134)[1])
        self.assertFalse(inspect("", "a public check",0)[1])

    def test_runner_keeps_generated_aot_intact(self):
        r=runner(LINK+"\n"+DONE+"\n  echo 'V295_BOUNDED_CANDIDATE inspected=0'"+"\n"+"echo 'V294_RESTORED_AOT verified=1'")
        self.assertIn("v298-harness.o",r)
        self.assertIn("analyze_v298_scope_native.py",r)
        self.assertIn("diagnose_v299_native_log.py",r)
        self.assertIn("analyze_v300_trace_hotspots.py",r)
        self.assertIn("analyze_v301_nand_first_helper.py",r)
        self.assertIn("V301_HELPER_AUDIT inspected=1",r)
        self.assertIn("restore_v302_private_helper.py",r)
        self.assertIn("V302_HELPER_CANDIDATE inspected=1",r)
        self.assertIn("V303_HELPER_NATIVE_LINK verified=1",r)
        self.assertIn("analyze_v304_helper_exec.py",r)
        self.assertIn("v303-native",r)
        self.assertIn("V304_EXEC_ATTEMPT inspected=1",r)
        self.assertIn("analyze_v306_helper_descendants.py",r)
        self.assertIn("V306_DESCENDANT_STAGE inspected=1",r)
        self.assertIn("analyze_v307_helper_abort.py",r)
        self.assertIn("V307_ABORT_CLASSIFIED inspected=1",r)
        self.assertIn("analyze_v309_native_edges.py",r)
        self.assertIn("V309_EDGE_STAGE inspected=1",r)
        self.assertIn("restore_v310_private_descendant.py",r)
        self.assertIn("analyze_v310_restored_coverage.py",r)
        self.assertIn("V310_NATIVE_TRIAL inspected=1",r)
        self.assertIn("v303-generated.o",r)
        self.assertIn("v294-generated.o",r)
        with self.assertRaises(ValueError):
            runner("unknown native candidate")

if __name__=="__main__":
    unittest.main()
