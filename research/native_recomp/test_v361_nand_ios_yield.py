#!/usr/bin/env python3
"""V361 synthetic-only original guest / native Starlet scheduling seam."""
import unittest
from derive_v361_nand_ios_yield import HEAD,PRIOR,MARKER,INJECTION,patch

SOURCE=(
    '#include "wii_ios_yield_scheduler.h"\n'
    "bool v250_candidate_mode=true;\n"
    "unsigned v250_nand_seen=1u;\n"
    "bool probe(){return v250_candidate_mode&&v250_nand_seen==1u;}\n"
    +HEAD+"\n"
    ' std::cout<<"V359_X1_CALL n="<<1u<<std::endl;\n'
    "}\n"
)

class Tests(unittest.TestCase):
    def test_one_original_restore_yield_only_when_authentic_request_pending(self):
        output=patch(SOURCE)
        self.assertEqual(output.count(MARKER),1)
        self.assertEqual(output.replace(HEAD+INJECTION,HEAD,1),SOURCE)
        for expected in (
            "v250_candidate_mode&&v250_nand_seen==1u",
            "addr==0x805265d4u",
            "ipc70_bus.pending_native_ios_request()",
            "ipc70_bus.read32(B::IPC+M::PPCMSG)",
            "ipc70_ram.valid(*msg,64u)",
            "(*msg&31u)==0u",
            "IosYieldScheduler scheduler(ipc70_bus)",
            "scheduler.service_one(ctx.msr)",
            "v361_logged<16u",
            "state.broadway_irq_level",
            "state.guest_exception_ready",
        ):
            self.assertIn(expected,INJECTION)
        for disallowed in (
            "ipc70_bus.write32","ctx.mmu.write","ctx.gpr[","ctx.pc=",
            "ctx.msr=", "ctx.is_running=false", "enter_external_irq(",
            "ctx.lr=", "ipc70_ram.write", "StmIos::Reply", "<<*msg",
            "return;", "throw ExceptionStop",
        ):
            self.assertNotIn(disallowed,INJECTION)

    def test_pending_original_request_is_fail_closed_on_invalid_pointer(self):
        self.assertIn('check(mapped,"V361 original NAND IOS request buffer became invalid")',INJECTION)
        self.assertIn("msg.has_value()&&*msg!=0u",INJECTION)
        self.assertNotIn("check(state.progress==",INJECTION)
        self.assertNotIn("state.progress=",INJECTION)

    def test_full_original_source_is_preserved_except_entry_injection(self):
        output=patch(SOURCE)
        self.assertIn(PRIOR,output)
        self.assertEqual(output.count(PRIOR),1)
        self.assertNotIn("V361_NAND_IOS_YIELD",SOURCE)

    def test_duplicate_and_missing_source_seams_rejected(self):
        for corrupt in (
            SOURCE.replace(HEAD,"",1),
            SOURCE+HEAD,
            SOURCE.replace(PRIOR,"changed",1),
            SOURCE.replace("wii_ios_yield_scheduler.h","irrelevant.h",1),
            SOURCE.replace("v250_candidate_mode","other_mode"),
            patch(SOURCE),
        ):
            with self.subTest(length=len(corrupt)):
                with self.assertRaises(ValueError):
                    patch(corrupt)

if __name__=="__main__":
    unittest.main()
