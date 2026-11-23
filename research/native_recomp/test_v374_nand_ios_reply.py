#!/usr/bin/env python3
"""V374 source-only authentic NAND scheduling source-mutation checks."""
import unittest
from derive_v374_nand_ios_reply import (
    HEAD,INCLUDE,NEW_INCLUDE,PRIOR,OTHER,MARKER,INJECTION,patch
)

FIXTURE=(
    INCLUDE+'\n'
    'bool v250_candidate_mode=true;\n'
    'unsigned v250_nand_seen=1u;\n'
    'bool nand(){return v250_candidate_mode&&v250_nand_seen==1u;}\n'
    +HEAD+'\n'
    'std::cout<<"V361_NAND_IOS_YIELD n=";\n'
    'std::cout<<"V373_NAND_IRQ_TIMELINE n=";\n'
    '}\n'
)

class Tests(unittest.TestCase):
    def test_exact_single_injection_and_reversible_guest_source(self):
        updated=patch(FIXTURE)
        self.assertEqual(updated.count(MARKER),1)
        self.assertEqual(updated.count(NEW_INCLUDE.strip()),1)
        self.assertEqual(
            updated.replace(HEAD+INJECTION,HEAD,1).replace(
                INCLUDE+'\n'+NEW_INCLUDE,INCLUDE,1),FIXTURE
        )
        self.assertIn(PRIOR,updated)
        self.assertIn(OTHER,updated)

    def test_real_guest_yield_and_hardware_guard_only(self):
        for required in (
            'v250_candidate_mode&&v250_nand_seen==1u',
            'addr==0x805265d4u',
            '!ipc70_bus.pending_native_ios_request()',
            'ipc70_bus.services().queued_replies()>0u',
            'B::IPC+M::PPCCTRL',
            'B::IPC+H::PPC_FLAG',
            'const bool yclear=',
            'const bool flagclear=',
            'const bool irq_before=',
            'service_deferred_reply_at_guest_boundary(',
            'ipc70_bus,ctx.msr',
            'v374_count<16u',
            'result.has_value()?result->progress:',
            '" queued="','" y1="','" eligible="'
        ):
            self.assertIn(required,INJECTION,required)

    def test_no_synthetic_guest_cpu_or_response(self):
        for forbidden in (
            'ipc70_bus.write32(', 'ipc70_bus.tick(', 'ctx.msr=',
            'ctx.pc=', 'ctx.gpr[', 'ctx.mmu.write',
            'ctx.is_running=', 'ctx.lr=', 'enter_external_irq(',
            'StmIos::Reply', 'ipc70_ram.write', 'throw ExceptionStop',
            '<<ctx.pc', '<<ctx.lr','<<ctx.msr','<<*prev_ctrl',
            'std::hex', 'service_one('
        ):
            self.assertNotIn(forbidden,INJECTION,forbidden)

    def test_missing_or_duplicate_seam_fails_closed(self):
        broken=(
            FIXTURE.replace(HEAD,''),
            FIXTURE+HEAD,
            FIXTURE.replace(INCLUDE,'#include "other.h"'),
            FIXTURE.replace(PRIOR,'prior_changed'),
            FIXTURE.replace(OTHER,'other_changed'),
            FIXTURE.replace('v250_candidate_mode','wrong_mode'),
            patch(FIXTURE),
        )
        for variant in broken:
            with self.subTest(size=len(variant)):
                with self.assertRaises(ValueError):
                    patch(variant)

if __name__=='__main__':
    unittest.main()
