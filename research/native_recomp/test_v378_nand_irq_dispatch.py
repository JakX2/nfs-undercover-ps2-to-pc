#!/usr/bin/env python3
"""V378 inspect original-free handler continuation and fail-closed source."""
import unittest
from derive_v377_nand_vector_handler import patch as v377_patch
from test_v377_nand_vector_handler import SOURCE as V377_FIXTURE
from derive_v378_nand_irq_dispatch import (
    patch,STATE_ADD,DISPATCH,NEW_STOP,OLD_STOP,MARKER,TRIAL
)
class Tests(unittest.TestCase):
    def test_original_handler_body_continues_without_guest_synthesis(self):
        source=v377_patch(V377_FIXTURE)
        derived=patch(source)
        self.assertEqual(derived.count(MARKER),1)
        self.assertEqual(derived.count(TRIAL),1)
        self.assertEqual(derived.count(NEW_STOP),1)
        self.assertNotIn(OLD_STOP,derived)
        self.assertIn('V377 original NAND vector never reached actual Wii handler entry',derived)
        self.assertIn('V160 did not execute original SC Y1 exception vector to handler',derived)
        self.assertIn('v378_dispatch_seen==1u',derived)
        self.assertEqual(derived.count('nwii::runtime::v378_dispatch_seen=0u;'),1)
        self.assertEqual(derived.count('nwii::runtime::v378_handler_inst=0u;'),1)
        self.assertLess(
            derived.index('nwii::runtime::v378_dispatch_seen=0u;'),
            derived.index('c.is_running=true;')
        )
        self.assertIn('c.pc==0x80526a3cu',derived)
        self.assertIn('continue; // finish this authenticated NAND-only bounded trial',derived)
        self.assertIn('c.is_running=true;',derived)
    def test_actual_dispatcher_guest_frame_only(self):
        for key in (
            'addr==0x80526a3cu', 'ctx.pc==addr','ctx.gpr[3]==4u',
            'ctx.mmu.read32(frame+408u)==v377_resume',
            'ctx.mmu.read32(frame+412u)==v377_srr1',
            'ctx.mmu.read32(frame+132u)==v377_lr',
            'ctx.mmu.read32(frame+136u)==v377_ctr',
            'ctx.mmu.read32(frame+140u)==v377_xer',
            'ctx.mmu.read32(frame+4u*i)==v377_gprs[i]',
            'ctx.inst_count>v378_handler_inst',
            'ctx.is_running=false;throw ExceptionStop{};',
        ):
            self.assertIn(key,DISPATCH)
        for key in ('ipc70_bus.tick(', 'service_one(', 'ipc70_bus.write32(',
                    'ctx.pc=', 'ctx.msr=', 'ctx.gpr[3]=','ctx.srr0=',
                    'StmIos::Invalid','run_game(ctx)'):
            if key.endswith('='):
                import re
                self.assertIsNone(re.search(r'\b'+re.escape(key)+r'(?!=)',DISPATCH))
            else:
                self.assertNotIn(key,DISPATCH)
    def test_fails_closed_against_old_abi_or_reapplication(self):
        source=v377_patch(V377_FIXTURE)
        for item in (
            source.replace('const bool v377_completed=','lost'),
            source.replace('V377_NAND_HANDLER_ENTRY vector=','lost'),
            source.replace('V377_NAND_HANDLER_TRIAL stopped=','lost'),
            source.replace('v377_handler_seen;','altered_counter;'),
            source.replace('nwii::runtime::v377_handler_seen=0u;','lost'),
            source.replace('ctx.is_running=false;throw ExceptionStop{};','lost'),
            patch(source)
        ):
            with self.assertRaises(ValueError):
                patch(item)
if __name__=='__main__':
    unittest.main()
