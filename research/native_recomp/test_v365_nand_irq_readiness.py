#!/usr/bin/env python3
"""Original-free V365 IRQ readiness probe source tests."""
import unittest
from derive_v365_nand_irq_readiness import HEAD, PRIOR, MARKER, INJECTION, patch

FIXTURE=(
    '#include "native_external_irq.h"\n'
    "bool v250_candidate_mode=true;\nunsigned v250_nand_seen=1u;\n"
    "bool fixture(){return v250_candidate_mode&&v250_nand_seen==1u;}\n"
    "uint8_t irq74_vector[8]={};\n"
    +HEAD+'\n std::cout<<"V361_NAND_IOS_YIELD n="<<1<<std::endl;\n}\n'
)

class Tests(unittest.TestCase):
    def test_exact_reversible_nonmutating_instrumentation(self):
        output=patch(FIXTURE)
        self.assertEqual(output.count(MARKER),1)
        self.assertEqual(output.replace(HEAD+INJECTION,HEAD,1),FIXTURE)
        for needed in (
            "v250_candidate_mode&&v250_nand_seen==1u",
            "ipc70_bus.external_irq_level()",
            "ipc70_bus.external_exception_pending(ctx.msr)",
            "v365_count<16u",
            "ctx.dispatch_saved_ctx",
            "ExternalUnsupportedMsr",
            "ExternalVector+uint32_t(i)",
            "ctx.mmu.get_ptr(at)",
            "ctx.mmu.read8(at)!=irq74_vector[i]",
            "eligible&&safe&&installed",
        ):
            self.assertIn(needed,INJECTION)
        for forbidden in (
            "enter_external_irq(", "service_one(", "ipc70_bus.tick(",
            "ipc70_bus.write32", "ctx.pc=", "ctx.msr=", "ctx.gpr[",
            "ctx.mmu.write", "ctx.is_running=", "return;", "<<ctx.pc",
            "std::hex", "signal_event(", "StmIos::Reply",
        ):
            self.assertNotIn(forbidden,INJECTION)

    def test_early_sc_request_is_not_observed_as_nand_readiness(self):
        self.assertIn("v250_candidate_mode&&v250_nand_seen==1u",INJECTION)
        self.assertIn("if(v365_count<16u)",INJECTION)
        self.assertIn("external_exception_pending(ctx.msr)",INJECTION)
        for candidate in (False,True):
            for nand in (False,True):
                observed=candidate and nand
                self.assertEqual(observed,all((candidate,nand)))

    def test_fail_closed_when_original_irq_context_is_missing(self):
        for altered in (
            FIXTURE.replace(HEAD,"",1),
            FIXTURE+HEAD,
            FIXTURE.replace(PRIOR,"unrelated",1),
            FIXTURE.replace("native_external_irq.h","wrong.h",1),
            FIXTURE.replace("irq74_vector","wrong_vector"),
            FIXTURE.replace("v250_candidate_mode","other_mode"),
            patch(FIXTURE),
        ):
            with self.subTest(size=len(altered)):
                with self.assertRaises(ValueError):
                    patch(altered)

if __name__=="__main__":
    unittest.main()
