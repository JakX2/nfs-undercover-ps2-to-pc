#!/usr/bin/env python3
"""V359 source-only probe tests."""
import unittest
from derive_v359_post_x1_call_probe import HEAD,PRIOR,MARKER,INJECTION,CATEGORIES,patch

FIXTURE=(
    "bool v250_candidate_mode=true;\n"
    "unsigned v250_nand_seen=1u;\n"
    "bool observer(){return v250_candidate_mode&&v250_nand_seen==1u;}\n"
    +HEAD+"\n"
    '  std::cout<<"V321_GUEST_ENTRY pc="<<0u<<std::endl;\n'
    "}\n"
)

class Tests(unittest.TestCase):
    def test_exact_reversible_bounded_nonmutating_probe(self):
        got=patch(FIXTURE)
        self.assertEqual(got.count(MARKER),1)
        self.assertEqual(got.replace(HEAD+INJECTION,HEAD,1),FIXTURE)
        self.assertIn("v359_count<16u",INJECTION)
        self.assertIn("ipc70_bus.pending_native_ios_request()",INJECTION)
        self.assertIn("if(pending||ipc70_bus.services().queued_replies()>0u)v359_armed=true",INJECTION)
        self.assertIn("v250_candidate_mode&&v250_nand_seen==1u",INJECTION)
        self.assertEqual(len(CATEGORIES),8)
        self.assertEqual(len({pc for pc,_ in CATEGORIES}),8)
        for pc,kind in CATEGORIES:
            self.assertIn(f"addr==0x{pc:08x}u)kind={kind}u",INJECTION)
        for illegal in ("ctx.gpr[","ctx.pc=","ctx.lr=","ctx.msr=","ctx.mmu.",
                        "ipc70_bus.write32","ipc70_bus.tick","service_one(",
                        "ctx.is_running", "std::hex", "<<addr","<<ctx.lr"):
            self.assertNotIn(illegal,INJECTION)

    def test_native_ack_retains_post_x1_census_visibility(self):
        # Real V361 IOS ACK drains X1 before the first later call can be
        # counted. A queued reply remains positive, read-only evidence.
        self.assertIn("pending||ipc70_bus.services().queued_replies()>0u",INJECTION)
        for pending in (False,True):
            for queued in (False,True):
                observed=pending or queued
                self.assertEqual(observed,not(not pending and not queued))
        self.assertNotIn("service_one(",INJECTION)
        self.assertNotIn("ipc70_bus.tick()",INJECTION)

    def test_bad_or_duplicate_seams_fail_closed(self):
        for bad in (FIXTURE.replace(HEAD,"",1),FIXTURE+HEAD,
                    FIXTURE.replace(PRIOR,"something_unrelated",1),
                    FIXTURE.replace("v250_candidate_mode","no_candidate"),
                    patch(FIXTURE)):
            with self.subTest(size=len(bad)):
                with self.assertRaises(ValueError):
                    patch(bad)

    def test_original_traces_remain_read_only(self):
        got=patch(FIXTURE)
        self.assertIn(PRIOR,got)
        self.assertEqual(got.count(PRIOR),1)
        self.assertNotIn("private",MARKER)
        self.assertNotIn("0x",MARKER)

if __name__=="__main__":
    unittest.main()
