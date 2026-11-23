#!/usr/bin/env python3
"""V373 original-free read-only NAND IRQ timeline injection tests."""
import unittest

from derive_v373_nand_irq_timeline import (
    HEAD, PRIOR, FLAG_ROUTE, MARKER, MAX_SAMPLES, INJECTION, patch,
)

FIXTURE = (
    '#include "native_external_irq.h"\n'
    'bool v250_candidate_mode=true;\n'
    'unsigned v250_nand_seen=1u;\n'
    'bool nand(){return v250_candidate_mode&&v250_nand_seen==1u;}\n'
    'uint8_t irq74_vector[8]={};\n'
    'void helper(){(void)ipc70_bus.services().queued_replies();}\n'
    + HEAD + '\n'
    ' std::cout<<"V370_NAND_FLAG_W1C n=";\n'
    ' std::cout<<"V365_IRQ_READY n=";\n'
    '}\n'
)

class Tests(unittest.TestCase):
    def test_injection_exactly_reversible(self):
        after=patch(FIXTURE)
        self.assertEqual(after.count(MARKER),1)
        self.assertEqual(after.replace(HEAD+INJECTION,HEAD,1),FIXTURE)
        self.assertEqual(MAX_SAMPLES,96)
        self.assertIn('v373_count<96u',INJECTION)

    def test_observes_ee_mask_and_irq_independently(self):
        for needed in (
            'v250_candidate_mode&&v250_nand_seen==1u',
            'ipc70_bus.services().queued_replies()>0u',
            '!ipc70_bus.pending_native_ios_request()',
            'ipc70_bus.external_irq_level()',
            'ipc70_bus.external_exception_pending(ctx.msr)',
            '(ctx.msr&B::MSR_EE)!=0u',
            'ctx.dispatch_saved_ctx',
            'irq74_vector.size()',
            'undercover::wii::ExternalVector',
            'ctx.mmu.get_ptr(at)',
            'ctx.mmu.read8(at)!=irq74_vector[i]',
            'M::Y1', 'M::Y2', 'H::IPC_PPC',
            '" ready="', '" ee="', '" irq="',
            '" flag="', '" queued="',
        ):
            self.assertIn(needed,INJECTION,needed)

    def test_no_ios_services_guest_mutations_or_secret_output(self):
        for forbidden in (
            'service_one(', 'ipc70_bus.tick(', 'ipc70_bus.write32(',
            'enter_external_irq(', 'signal_event(', 'ctx.gpr[',
            'ctx.msr=', 'ctx.pc=', 'ctx.is_running=', 'ctx.mmu.write',
            'ipc70_ram.write', 'StmIos::Reply', 'throw ExceptionStop',
            'std::hex', '<<at', '<<ctx.pc', '<<ctx.lr', '<<ctx.gpr',
            '<<ctx.msr', '<<irq74_vector[i]',
        ):
            self.assertNotIn(forbidden,INJECTION,forbidden)

    def test_missing_or_changed_original_source_fails_closed(self):
        for bad in (
            FIXTURE.replace(HEAD,'',1),
            FIXTURE + HEAD,
            FIXTURE.replace(PRIOR,'different',1),
            FIXTURE.replace(FLAG_ROUTE,'different',1),
            FIXTURE.replace('native_external_irq.h','other.h',1),
            FIXTURE.replace('irq74_vector','missing_vector'),
            FIXTURE.replace('v250_candidate_mode','wrong_phase'),
            FIXTURE.replace('ipc70_bus.services().queued_replies()', 'different_queue'),
            patch(FIXTURE),
        ):
            with self.subTest(length=len(bad)):
                with self.assertRaises(ValueError):
                    patch(bad)

if __name__=="__main__":
    unittest.main()
