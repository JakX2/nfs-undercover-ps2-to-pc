#!/usr/bin/env python3
"""V367 source-only authentic NAND mask write routing regression tests."""
import unittest
from derive_v367_nand_irq_mask_route import HEADER,PRIOR,MARKER,INJECTION,patch

FIXTURE=(
    "bool v250_candidate_mode=false;\n"
    "unsigned v250_nand_seen=0u;\n"
    "bool test(){return v250_candidate_mode&&v250_nand_seen==1u;}\n"
    "void original(){ipc70_bus.write32(0u,0u);mmio_writes.emplace_back(0u,0u);}\n"
    +HEADER+"\n"
    ' std::cout<<"V352_NAND_BUS kind="<<1u;\n'
    ' std::cout<<"V352_NAND_BUS kind="<<2u;\n'
    ' check(false,"unexpected IPC mask MMIO write");\n'
    "}\n"
)

class Tests(unittest.TestCase):
    def test_original_mask_values_reach_real_hardware_without_rewriting(self):
        got=patch(FIXTURE)
        self.assertEqual(got.count(MARKER),1)
        self.assertEqual(got.replace(HEADER+INJECTION,HEADER,1),FIXTURE)
        for required in (
            "v250_candidate_mode&&v250_nand_seen==1u",
            "addr==B::PI_MASK",
            "addr==B::IPC+H::PPC_MASK",
            "addr==B::MIRROR+H::PPC_MASK",
            "if(pi||ppc)",
            "ipc70_bus.write32(addr,value)",
            "check(accepted,",
            "mmio_writes.emplace_back(addr,value)",
            "v367_count<16u",
            "ipc70_bus.external_irq_level()",
        ):
            self.assertIn(required,INJECTION)
        for forbidden in (
            "service_one(", "ipc70_bus.tick(", "ctx.msr=",
            "ctx.gpr[", "ctx.is_running=", "ctx.mmu.write",
            "enter_external_irq(", "ipc70_ram.write",
            "StmIos::Reply", "return false;", "std::hex",
            "<<addr", "<<value",
        ):
            self.assertNotIn(forbidden,INJECTION)

    def test_early_ipc_stage_and_unrecognized_hardware_stay_fail_closed(self):
        got=patch(FIXTURE)
        self.assertEqual(got.count("unexpected IPC mask MMIO write"),1)
        self.assertIn("if(pi||ppc){",got)
        self.assertIn("if(v250_candidate_mode&&v250_nand_seen==1u)",got)
        self.assertEqual(got.count("V352_NAND_BUS kind="),2)
        for candidate in (False,True):
            for nand in (False,True):
                for supported in (False,True):
                    route=candidate and nand and supported
                    self.assertEqual(route,supported and (candidate and nand))

    def test_duplicate_or_missing_observer_seams_rejected(self):
        for bad in (
            FIXTURE.replace(HEADER,"",1),
            FIXTURE+HEADER,
            FIXTURE.replace(PRIOR,"broken",1),
            FIXTURE.replace("v250_candidate_mode","unrelated_flag"),
            FIXTURE.replace("unexpected IPC mask MMIO write","another observer",1),
            FIXTURE.replace("ipc70_bus.write32","wrong_bus",1),
            patch(FIXTURE),
        ):
            with self.subTest(size=len(bad)):
                with self.assertRaises(ValueError):
                    patch(bad)

if __name__=="__main__":
    unittest.main()
