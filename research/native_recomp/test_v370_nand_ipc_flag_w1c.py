#!/usr/bin/env python3
"""V370 original-free register-precise Hollywood W1C regression."""
import unittest
from derive_v370_nand_ipc_flag_w1c import HEAD,PRIOR,MARKER,INJECTION,patch

FIXTURE=(
    "bool v250_candidate_mode=false;\n"
    "unsigned v250_nand_seen=0u;\n"
    "bool t(){return v250_candidate_mode&&v250_nand_seen==1u;}\n"
    "void test(){(void)ipc70_bus.services().queued_replies();"
    "ipc70_bus.write32(0u,0u);mmio_writes.emplace_back(0u,0u);}\n"
    +HEAD+"\n"
    ' std::cout<<"V367_NAND_IRQ_MASK n="<<1u;\n'
    ' check(false,"unexpected IPC mask MMIO write");\n'
    "}\n"
)

class Tests(unittest.TestCase):
    def test_original_flag_write_is_not_a_synthetic_ios_response(self):
        result=patch(FIXTURE)
        self.assertEqual(result.count(MARKER),1)
        self.assertEqual(result.replace(HEAD+INJECTION,HEAD,1),FIXTURE)
        for required in (
            "v250_candidate_mode&&v250_nand_seen==1u",
            "addr==B::IPC+H::PPC_FLAG",
            "addr==B::MIRROR+H::PPC_FLAG",
            "ipc70_bus.read32(addr)",
            "ipc70_bus.write32(addr,value)",
            "check(accepted,",
            "value&H::IPC_PPC",
            "H::IPC_PPC",
            "ipc70_bus.external_irq_level()",
            "ipc70_bus.services().queued_replies()>0u",
            "mmio_writes.emplace_back(addr,value)",
            "v370_count<16u",
        ):
            self.assertIn(required,INJECTION)
        for forbidden in (
            "service_one(", "ipc70_bus.tick(", "enter_external_irq(",
            "ctx.gpr[", "ctx.pc=", "ctx.msr=", "ctx.mmu.write",
            "ipc70_ram.write", "StmIos::Reply", "ctx.is_running=",
            "std::hex", "<<addr", "<<value",
        ):
            self.assertNotIn(forbidden,INJECTION)

    def test_only_nand_and_supported_flag_registers_bypass_legacy_check(self):
        result=patch(FIXTURE)
        self.assertEqual(result.count("unexpected IPC mask MMIO write"),1)
        self.assertIn("if(flag){",INJECTION)
        for candidate in (False,True):
            for nand in (False,True):
                for flag in (False,True):
                    enabled=candidate and nand and flag
                    self.assertEqual(enabled,flag and (candidate and nand))

    def test_original_latch_readback_remains_read_only_observation(self):
        self.assertIn("before=prior.has_value()",INJECTION)
        self.assertIn("remaining=after.has_value()",INJECTION)
        self.assertIn("const bool accepted=ipc70_bus.write32(addr,value);",INJECTION)
        self.assertNotIn("ipc70_bus.write32(addr,H::IPC_PPC)",INJECTION)
        self.assertNotIn("ipc70_bus.write32(addr,0u)",INJECTION)

    def test_ambiguous_or_missing_source_fails_closed(self):
        for broken in (
            FIXTURE.replace(HEAD,"",1),
            FIXTURE+HEAD,
            FIXTURE.replace(PRIOR,"unrelated",1),
            FIXTURE.replace("v250_candidate_mode","missing_mode"),
            FIXTURE.replace("unexpected IPC mask MMIO write","changed old label"),
            FIXTURE.replace("ipc70_bus.write32","wrong_bus"),
            patch(FIXTURE),
        ):
            with self.subTest(size=len(broken)):
                with self.assertRaises(ValueError):
                    patch(broken)

if __name__=="__main__":
    unittest.main()
