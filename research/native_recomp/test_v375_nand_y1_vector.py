#!/usr/bin/env python3
"""V375 original-free source seam and PowerPC exception boundary review."""
import unittest
from derive_v375_nand_y1_vector import HEAD,PRIOR,TIMELINE,MARKER,INJECTION,patch

FIXTURE=(
    '#include "native_external_irq.h"\n'
    'bool v250_candidate_mode=true;\n'
    'unsigned v250_nand_seen=1u;\n'
    'auto g(){return v250_candidate_mode&&v250_nand_seen==1u;}\n'
    'auto irq74_vector=1;\n'
    +HEAD+'\n'
    'std::cout<<"V374_NAND_REPLY_GATE n=";\n'
    'std::cout<<"V373_NAND_IRQ_TIMELINE n=";\n'
    '}\n'
)

class Tests(unittest.TestCase):
    def test_reversible_exact_single_irq_guard(self):
        altered=patch(FIXTURE)
        self.assertEqual(altered.count(MARKER),1)
        self.assertEqual(altered.replace(HEAD+INJECTION,HEAD,1),FIXTURE)
        self.assertEqual(altered.count(PRIOR),1)
        self.assertEqual(altered.count(TIMELINE),1)

    def test_only_real_hardware_y1_and_original_guest_boundary(self):
        for anchor in (
            'v250_candidate_mode&&v250_nand_seen==1u',
            '!ipc70_bus.pending_native_ios_request()',
            'ipc70_bus.external_exception_pending(ctx.msr)',
            'B::IPC+M::PPCCTRL','B::IPC+H::PPC_FLAG',
            '((*ctrl&M::Y1)!=0u)','((*ctrl&M::Y2)==0u)',
            '((*flag&H::IPC_PPC)!=0u)',
            'ctx.pc==addr','!(ctx.pc&3u)','!ctx.dispatch_saved_ctx',
            '!(ctx.msr&undercover::wii::ExternalUnsupportedMsr)',
            'irq74_vector[i]',
            'enter_external_irq(', 'ctx,ipc70_bus,irq74_vector,true',
            'ctx.srr0==resume','ctx.srr1==',
            'ctx.msr==(msr&~undercover::wii::ExternalMsrClear)',
            'ctx.gpr==gprs','ctx.lr==lr','ctx.ctr==ctr','ctx.xer==xer',
            'ctx.is_running=false;throw ExceptionStop{};',
        ):
            self.assertIn(anchor,INJECTION,anchor)

    def test_no_fake_ios_reply_or_guest_register_override(self):
        import re
        for bad in (
            'ipc70_bus.tick(', 'service_one(', 'ipc70_bus.write32(',
            'ipc70_ram.write32(', 'run_game(ctx)', 'ctx.is_running=true',
            'ctx.mmu.write', '<<ctx.pc','<<ctx.lr','<<ctx.msr',
            'StmIos::Reply', 'StmIos::Open','IOS::Invalid'
        ):
            self.assertNotIn(bad,INJECTION,bad)
        for register in ('pc','msr','lr','ctr','srr0','srr1','inst_count'):
            self.assertIsNone(re.search(r'\bctx\.'+register+r'\s*=(?!=)',INJECTION),register)
        self.assertIsNone(re.search(r'\bctx\.gpr\s*\[\s*3\s*\]\s*=(?!=)',INJECTION))

    def test_changed_authentication_seams_fail_closed(self):
        variants=(
            FIXTURE.replace(HEAD,''),
            FIXTURE+HEAD,
            FIXTURE.replace(PRIOR,'lost'),
            FIXTURE.replace(TIMELINE,'lost'),
            FIXTURE.replace('native_external_irq.h','missing.h'),
            FIXTURE.replace('v250_candidate_mode','missing'),
            patch(FIXTURE),
        )
        for item in variants:
            with self.assertRaises(ValueError):
                patch(item)

if __name__=="__main__":
    unittest.main()
