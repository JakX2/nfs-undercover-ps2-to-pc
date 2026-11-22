#!/usr/bin/env python3
"""V298 original-free phase scope, privacy and regression guards."""
import unittest
from derive_v298_scope_reply_observer import (OLD,NEW,CHECK,SUBMIT_OLD,SUBMIT_NEW,
                                                CLIENT_OLD,CLIENT_NEW,IOS_OPEN_OLD,IOS_OPEN_NEW,
                                                IOS_OPEN_LABEL,IOS_OPEN_EXPLICIT,IOS_TRACE_OLD,IOS_TRACE_NEW,
                                                ASYNC_OLD,ASYNC_NEW,ASYNC_LABEL,
                                                ARENA_OLD,ARENA_NEW,ARENA_LABEL,
                                                SRAM_OLD,SRAM_NEW,SRAM_LABEL,
                                                TRANSPORT_OLD,TRANSPORT_NEW,TRANSPORT_LABEL,
                                                NAND_SC_OLD,NAND_SC_NEW,NAND_SC_LABEL,
                                                VECTOR_TRACE_OLD,VECTOR_TRACE_NEW,VECTOR_TRACE_LABEL,
                                                NAND_IRQ_OLD,NAND_IRQ_NEW,NAND_IRQ_LABEL,
                                                NAND_QUEUE_OLD,NAND_QUEUE_NEW,NAND_QUEUE_LABEL,
                                                NAND_SEND_OLD,NAND_SEND_NEW,NAND_SEND_LABEL,summarize_seams,
                                                choose_ios_tail,patch as scope)
from derive_v298_scoped_nand_runner import LINK,DONE,patch as runner
from derive_v114_sc_flush_syscall_harness import EDITS as V114_EDITS
from analyze_v298_scope_native import inspect

SOURCE=(OLD+"\n"+SUBMIT_OLD+"\n"+CLIENT_OLD+"\n"+IOS_OPEN_OLD+
        '\n      check(false,"native IOS_Open allocator tail entry differs");\n'+
        IOS_OPEN_EXPLICIT+"\n"+IOS_TRACE_OLD+"\n"+ASYNC_OLD+
        '\n       check(false,"V112 original IOS_OpenAsync allocator disable differs");\n'+
        CHECK+"\n"+ARENA_OLD+"\n"+ARENA_LABEL+"\n"+
        SRAM_OLD+"\n"+SRAM_LABEL+"\n"+TRANSPORT_OLD+
        '\n       check(false,"V113 original IOS transport did not reach bounded cache flush");\n'+
        "\nV296_SERVICE_ENTRY kind=\nv250_nand_seen\n"+NAND_SC_OLD+"\n"+
        VECTOR_TRACE_OLD+"\n     ctx.lr==(arena_active?arena_flush_lr(arena_phase):0x80522044u)&&\n"+
        VECTOR_TRACE_LABEL+"\n    ++sc_vector_entries;\n  }\n"+NAND_IRQ_OLD+
        '\n     check(false,"V115 original IOS submission IRQ-disable call differs");\n'+
        NAND_QUEUE_OLD+
        '\n     check(false,"V116 original IOS request queue-helper boundary differs");\n'+
        NAND_SEND_OLD+
        '\n     check(false,"V117 original IPC send register call ABI differs");\n')
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
        self.assertIn(IOS_OPEN_LABEL,s)
        self.assertIn(IOS_TRACE_NEW,s)
        self.assertIn(ASYNC_NEW,s)
        self.assertIn(ASYNC_LABEL,s)
        self.assertIn(ARENA_NEW,s)
        self.assertIn(SRAM_NEW,s)
        self.assertIn(TRANSPORT_NEW,s)
        self.assertIn(TRANSPORT_LABEL,s)
        self.assertNotIn(TRANSPORT_OLD,s)
        self.assertNotIn(ARENA_OLD,s)
        self.assertNotIn(SRAM_OLD,s)
        self.assertNotIn(ASYNC_OLD,s)
        self.assertNotIn(IOS_TRACE_OLD,s)
        self.assertNotIn(IOS_OPEN_OLD,s)
        self.assertEqual(s.count(IOS_OPEN_NEW),1)
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
        self.assertIn("reply=1 submit=1 client=1 ios=1 ios_label=1 ios_call=1 async=1 async_label=1 arena=1 sram=1 transport=1 transport_label=1 nand_sc=1 nand_sc_label=1 vector=1 vector_label=1 explicit=1",good)
        self.assertIn("check=1 service=1 nand=1",good)
        self.assertIn("near=1",good)
        self.assertIn("nand_sc=1 nand_sc_label=1",good)
        self.assertIn("vector=1 vector_label=1",good)
        self.assertIn('ios_label=1',good)
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
            "if(addr==0x8051ad38u&&"
            "!(v250_candidate_mode&&v250_nand_seen==1u)){"
        )
        for open_active,candidate,nand_seen,expected in cases:
            observed=open_active and not(candidate and nand_seen)
            self.assertEqual(observed,expected)
        with self.assertRaises(ValueError):
            scope(SOURCE.replace(IOS_OPEN_OLD,"",1))
        duplicate=scope(SOURCE+"\n"+IOS_OPEN_OLD)
        self.assertEqual(duplicate.count(IOS_OPEN_NEW),1)
        self.assertEqual(duplicate.count(IOS_OPEN_OLD),1)
        ambiguous=SOURCE.replace(IOS_OPEN_OLD,IOS_OPEN_OLD+"\n"+IOS_OPEN_OLD,1)
        self.assertIn("near=2",summarize_seams(ambiguous))
        with self.assertRaises(ValueError):
            scope(ambiguous)
        with self.assertRaises(ValueError):
            scope(SOURCE.replace(IOS_OPEN_EXPLICIT,"",1))

    def test_v316_unique_v71_label_selects_only_correct_branch(self):
        original=choose_ios_tail(SOURCE)
        self.assertEqual(SOURCE[original:original+len(IOS_OPEN_OLD)],IOS_OPEN_OLD)
        prefix=IOS_OPEN_OLD+"\n"+("x"*400)+"\n"
        candidate=scope(prefix+SOURCE)
        self.assertEqual(candidate.count(IOS_OPEN_NEW),1)
        self.assertEqual(candidate.count(IOS_OPEN_OLD),1)
        with self.assertRaises(ValueError):
            choose_ios_tail(SOURCE.replace(IOS_OPEN_LABEL,"not the assertion"))

    def test_v318_ios_open_callsite_phase_guard(self):
        self.assertEqual(
            IOS_TRACE_NEW,
            "if((!v250_candidate_mode||v250_nand_seen==0u)&&"
            "open71_trace(addr,ctx))return;"
        )
        for candidate in (False,True):
            for nand_seen in (False,True):
                allowed=not candidate or not nand_seen
                self.assertEqual(
                    (not candidate) or (nand_seen==False),allowed
                )
        original=scope(SOURCE)
        self.assertEqual(original.count(IOS_TRACE_NEW),1)
        self.assertIn(IOS_OPEN_EXPLICIT,original)
        for broken in (SOURCE.replace(IOS_TRACE_OLD,"",1),
                       SOURCE+"\n"+IOS_TRACE_OLD):
            with self.assertRaises(ValueError):
                scope(broken)

    def test_v320_original_sc_async_observer_phase_scope(self):
        self.assertEqual(
            ASYNC_NEW,
            "if(post111_open==1u&&post110_chosen==2u&&\n"
            "       (!v250_candidate_mode||v250_nand_seen==0u)){"
        )
        output=scope(SOURCE)
        self.assertEqual(output.count(ASYNC_NEW),1)
        self.assertEqual(output.count(ASYNC_LABEL),1)
        self.assertNotIn(ASYNC_OLD,output)
        for candidate in (False,True):
            for seen in (False,True):
                enabled=(not candidate or not seen)
                self.assertEqual(enabled,not(candidate and seen))
        for malformed in (
            SOURCE.replace(ASYNC_OLD,"",1),
            SOURCE+"\n"+ASYNC_OLD,
            SOURCE.replace(ASYNC_LABEL,"unrelated assertion",1),
        ):
            with self.subTest(malformed=len(malformed)):
                with self.assertRaises(ValueError):
                    scope(malformed)

    def test_v322_legacy_cache_observers_do_not_intercept_nand(self):
        candidate=scope(SOURCE)
        self.assertEqual(candidate.count(ARENA_NEW),1)
        self.assertEqual(candidate.count(SRAM_NEW),1)
        self.assertEqual(candidate.count(ARENA_LABEL),1)
        self.assertEqual(candidate.count(SRAM_LABEL),1)
        self.assertIn("addr==0x805222c0u",ARENA_NEW)
        self.assertNotIn("if(arena_active)",ARENA_OLD)
        self.assertIn(ARENA_NEW,scope(SOURCE.replace(ARENA_OLD,ARENA_OLD+"\n     if(arena_active){",1)))
        self.assertIn("addr==0x80522294u",SRAM_NEW)
        self.assertNotIn("ctx.gpr[3] =",ARENA_NEW+SRAM_NEW)
        self.assertNotIn("ctx.mmu.write",ARENA_NEW+SRAM_NEW)
        for enabled in (False,True):
            for nand in (False,True):
                guarded=(not enabled or not nand)
                self.assertEqual(guarded,not(enabled and nand))
        for changed in (
            SOURCE.replace(ARENA_OLD,"",1),
            SOURCE.replace(SRAM_OLD,"",1),
            SOURCE.replace(ARENA_LABEL,"unrelated assertion",1),
            SOURCE.replace(ARENA_OLD,"if(addr==0x805222c0u){",1),
            SOURCE.replace(SRAM_LABEL,"unrelated assertion",1),
            SOURCE+"\n"+SRAM_OLD,
        ):
            with self.subTest(length=len(changed)):
                with self.assertRaises(ValueError):
                    scope(changed)

    def test_v328_original_sc_transport_arrival_guard(self):
        # Historical V113 is an intentional bounded test STOP, not an
        # actual IOS service implementation.
        self.assertEqual(
            TRANSPORT_NEW,
            "if(post112_submit==1u&&addr==0x805222c0u&&ctx.lr==0x8051963cu&&\n"
            "       (!v250_candidate_mode||v250_nand_seen==0u)){"
        )
        changed=scope(SOURCE)
        self.assertEqual(changed.count(TRANSPORT_NEW),1)
        self.assertEqual(changed.count(TRANSPORT_LABEL),1)
        self.assertNotIn(TRANSPORT_OLD,changed)
        for candidate_mode in (False,True):
            for nand_seen in (False,True):
                observe_old=(not candidate_mode or not nand_seen)
                self.assertEqual(observe_old,not(candidate_mode and nand_seen))
        for malformed in (
            SOURCE.replace(TRANSPORT_OLD,"",1),
            SOURCE+"\n"+TRANSPORT_OLD,
            SOURCE.replace(TRANSPORT_LABEL,"different assertion",1),
        ):
            with self.subTest(size=len(malformed)):
                with self.assertRaises(ValueError):
                    scope(malformed)

    def test_v329_v114_transport_anchor_provenance(self):
        # V113 first uses POST_OWNER, then V114 rewrites the exact
        # bounded observer to a fixed cache-flush entry. The V298
        # patch sees the final generated harness, never the V113 input.
        self.assertIn(
            ("if(post112_submit==1u&&addr==POST_OWNER&&ctx.lr==0x8051963cu){",
             TRANSPORT_OLD),
            V114_EDITS)
        self.assertEqual(scope(SOURCE).count(TRANSPORT_NEW),1)
        stale=SOURCE.replace(
            TRANSPORT_OLD,
            "if(post112_submit==1u&&addr==POST_OWNER&&ctx.lr==0x8051963cu){",
            1)
        self.assertIn("transport=0",summarize_seams(stale))
        with self.assertRaises(ValueError):
            scope(stale)

    def test_v331_native_nand_sc_uses_real_vector_without_old_counters(self):
        scoped=scope(SOURCE)
        self.assertEqual(scoped.count(NAND_SC_NEW),1)
        self.assertEqual(scoped.count(NAND_SC_LABEL),1)
        self.assertIn("native_idle_cache_sc(ctx,SYSCALL_DEST,sc_vector,",NAND_SC_NEW)
        self.assertIn("!ipc70_bus.external_irq_level()",NAND_SC_NEW)
        self.assertIn("func_80000C00(c)",NAND_SC_NEW)
        self.assertIn("if(v250_candidate_mode&&v250_nand_seen==1u)",NAND_SC_NEW)
        self.assertIn("check(submit72_flush==1u&&submit72_sc==0u",NAND_SC_NEW)
        self.assertIn("ctx.msr==msr&&ctx.lr==lr",NAND_SC_NEW)
        self.assertNotIn("ctx.mmu.write",NAND_SC_NEW)
        self.assertNotIn("ctx.gpr[3]=",NAND_SC_NEW)
        for mode in (False,True):
            for seen in (False,True):
                self.assertEqual(mode and seen,bool(mode and seen))
        for broken in (
            SOURCE.replace(NAND_SC_OLD,"",1),
            SOURCE+"\\n"+NAND_SC_OLD,
            SOURCE.replace(NAND_SC_LABEL,"different assertion",1),
        ):
            with self.subTest(size=len(broken)):
                with self.assertRaises(ValueError):
                    scope(broken)

    def test_v332_nand_sc_vector_observer_keeps_guest_exception(self):
        # The old boot assertion checks the DSP/arena callsite and counts.
        # It is not a universal rule for this authentic NAND cache syscall.
        scoped=scope(SOURCE)
        self.assertEqual(scoped.count(VECTOR_TRACE_NEW),1)
        self.assertEqual(scoped.count(VECTOR_TRACE_LABEL),1)
        self.assertNotIn(VECTOR_TRACE_OLD,scoped)
        self.assertIn("v250_candidate_mode&&v250_nand_seen==1u&&ctx.lr==0x8051963cu",
                      VECTOR_TRACE_NEW)
        self.assertIn("ctx.srr0==0x805222ecu&&ctx.pc==0x80000c00u",
                      VECTOR_TRACE_NEW)
        self.assertIn("!(ctx.msr&0x8000u)",VECTOR_TRACE_NEW)
        self.assertIn("return; // Observer only:",VECTOR_TRACE_NEW)
        self.assertIn("native_idle_cache_sc",NAND_SC_NEW)
        # The older OSInit vector assertion remains in the else branch.
        self.assertIn("ctx.lr==(arena_active?arena_flush_lr(arena_phase):0x80522044u)",
                      scoped)
        self.assertIn("++sc_vector_entries;",VECTOR_TRACE_NEW+"\n"+SOURCE)
        for candidate in (False,True):
            for nand_seen in (False,True):
                for callsite in (0x8051963c,0x80522044):
                    special=candidate and nand_seen and callsite==0x8051963c
                    self.assertEqual(special, candidate and nand_seen and callsite==0x8051963c)
        for altered in (
            SOURCE.replace(VECTOR_TRACE_OLD,"",1),
            SOURCE+"\n"+VECTOR_TRACE_OLD,
            SOURCE.replace(VECTOR_TRACE_LABEL,"different vector assertion",1),
        ):
            with self.subTest(length=len(altered)):
                with self.assertRaises(ValueError):
                    scope(altered)

    def test_v334_nand_irq_disable_phase_scope_keeps_original_call(self):
        # V115's earlier request counters are not a global contract for
        # the genuine 0x80519640 NAND submission callsite.
        scoped=scope(SOURCE)
        self.assertEqual(scoped.count(NAND_IRQ_NEW),1)
        self.assertEqual(scoped.count(NAND_IRQ_LABEL),1)
        self.assertNotIn(NAND_IRQ_OLD,scoped)
        self.assertIn("post115_sc==1u",NAND_IRQ_NEW)
        self.assertIn("addr==INT_DISABLE&&ctx.lr==0x80519640u",NAND_IRQ_NEW)
        self.assertIn("(!v250_candidate_mode||v250_nand_seen==0u)",NAND_IRQ_NEW)
        self.assertNotIn("ctx.gpr[",NAND_IRQ_NEW)
        self.assertNotIn("ctx.msr=",NAND_IRQ_NEW)
        self.assertNotIn("ctx.is_running=false",NAND_IRQ_NEW)
        for candidate in (False,True):
            for nand in (False,True):
                self.assertEqual(not(candidate and nand),
                                 (not candidate or not nand))
        for bad in (
            SOURCE.replace(NAND_IRQ_OLD,"",1),
            SOURCE+"\n"+NAND_IRQ_OLD,
            SOURCE.replace(NAND_IRQ_LABEL,"unrelated IRQ assertion",1),
        ):
            with self.subTest(size=len(bad)):
                with self.assertRaises(ValueError):
                    scope(bad)

    def test_v337_queue_helper_scopes_only_earlier_observer(self):
        # The V117-generated harness continues the original queue helper,
        # not a synthetic success path, on the genuine NAND callsite.
        scoped=scope(SOURCE)
        self.assertEqual(scoped.count(NAND_QUEUE_NEW),1)
        self.assertEqual(scoped.count(NAND_QUEUE_LABEL),1)
        self.assertNotIn(NAND_QUEUE_OLD,scoped)
        self.assertIn("addr==0x8051afe0u&&ctx.lr==0x805196d4u",NAND_QUEUE_NEW)
        self.assertIn("post115_disable==1u",NAND_QUEUE_NEW)
        self.assertIn("(!v250_candidate_mode||v250_nand_seen==0u)",NAND_QUEUE_NEW)
        self.assertNotIn("ctx.is_running=false",NAND_QUEUE_NEW)
        self.assertNotIn("post116_queue++",NAND_QUEUE_NEW)
        self.assertNotIn("ctx.gpr[",NAND_QUEUE_NEW)
        for candidate in (False,True):
            for nand in (False,True):
                # Earlier SC request must retain its original strict probe.
                enabled=not(candidate and nand)
                self.assertEqual(enabled,(not candidate or not nand))
        for bad in (
            SOURCE.replace(NAND_QUEUE_OLD,"",1),
            SOURCE+"\n"+NAND_QUEUE_OLD,
            SOURCE.replace(NAND_QUEUE_LABEL,"changed old queue label",1),
        ):
            with self.subTest(length=len(bad)):
                with self.assertRaises(ValueError):
                    scope(bad)

    def test_v338_send_register_phase_scope_preserves_real_mmio(self):
        # V117's earlier request check does not describe NAND counters.
        # Its observer can be retired without altering the real HW_Reg_Write32.
        scoped=scope(SOURCE)
        self.assertEqual(scoped.count(NAND_SEND_NEW),1)
        self.assertEqual(scoped.count(NAND_SEND_LABEL),1)
        self.assertNotIn(NAND_SEND_OLD,scoped)
        self.assertIn("addr==0x8051906cu&&ctx.lr==0x80519780u",NAND_SEND_NEW)
        self.assertIn("post116_queue==1u",NAND_SEND_NEW)
        self.assertIn("(!v250_candidate_mode||v250_nand_seen==0u)",NAND_SEND_NEW)
        for disallowed in ("ctx.is_running=false", "HW_Reg_Write32", "ctx.gpr[", "ipc70_bus.write32", "post117_send++"):
            self.assertNotIn(disallowed,NAND_SEND_NEW)
        for candidate in (False,True):
            for nand in (False,True):
                enabled = not (candidate and nand)
                self.assertEqual(enabled,(not candidate or not nand))
        for modified in (
            SOURCE.replace(NAND_SEND_OLD,"",1),
            SOURCE+"\n"+NAND_SEND_OLD,
            SOURCE.replace(NAND_SEND_LABEL,"changed old send-reg label",1),
        ):
            with self.subTest(size=len(modified)):
                with self.assertRaises(ValueError):
                    scope(modified)

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
        self.assertIn("audit_v317_descendant_edges.py",r)
        self.assertIn("V317_STAGE inspected=1",r)
        self.assertIn("analyze_v323_second_descendants.py",r)
        self.assertIn("V323_STAGE inspected=1",r)
        self.assertIn("analyze_v326_third_descendants.py",r)
        self.assertIn("V326_STAGE inspected=1",r)
        self.assertIn("audit_v319_native_entries.py",r)
        self.assertIn("V319_ENTRY_STAGE inspected=1",r)
        self.assertIn("analyze_v333_nand_cache_native.py",r)
        self.assertIn("V333_CACHE_STAGE inspected=1",r)
        self.assertIn("analyze_v335_nand_ipc_frontier.py",r)
        self.assertIn("V335_IPC_STAGE inspected=1",r)
        self.assertIn("derive_v321_guest_entry_probe.py",r)
        self.assertIn("analyze_v321_native_entry_comparison.py",r)
        self.assertIn("V321_ENTRY_COMPARE inspected=1",r)
        self.assertIn("v303-generated.o",r)
        self.assertIn("v294-generated.o",r)
        with self.assertRaises(ValueError):
            runner("unknown native candidate")

if __name__=="__main__":
    unittest.main()
