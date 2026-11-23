#!/usr/bin/env python3
"""V379 original-free source guard and unchanged guest/runtime proof."""
import unittest
from derive_v377_nand_vector_handler import patch as make_v377
from derive_v378_nand_irq_dispatch import patch as make_v378
from test_v377_nand_vector_handler import SOURCE
from derive_v379_nand_timebase_frontier import (
    patch, TRACE, MARKER, TRIAL, OLD_STOP, NEW_STOP
)

class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original=make_v378(make_v377(SOURCE))

    def test_original_dispatcher_continues_to_actual_timebase(self):
        output=patch(self.original)
        self.assertEqual(output.count(MARKER),1)
        self.assertEqual(output.count(TRIAL),1)
        self.assertEqual(output.count(NEW_STOP),1)
        self.assertNotIn(OLD_STOP,output)
        self.assertIn('addr==0x8052a824u',output)
        self.assertIn('ctx.lr==0x80526c84u',output)
        self.assertIn('c.pc==0x8052a824u',output)
        self.assertIn('v379_time_seen==1u',output)
        self.assertIn('V160 did not execute original SC Y1 exception vector to handler',output)
        self.assertIn('V378_NAND_DISPATCH_ENTRY route=',output)
        self.assertIn('V377_NAND_HANDLER_ENTRY vector=',output)

    def test_no_synthetic_ios_reply_or_guest_mutation(self):
        for needed in (
            'ipc70_bus.external_irq_level()',
            '((*ctrl&M::Y1)!=0u)', '((*ctrl&M::Y2)==0u)',
            '((*flag&H::IPC_PPC)!=0u)',
            'ctx.pc==addr', 'ctx.lr==0x80526c84u',
            'ctx.inst_count>v379_dispatch_inst',
            'ctx.is_running=false;throw ExceptionStop{};'
        ):
            self.assertIn(needed,TRACE)
        for forbidden in (
            'ipc70_bus.write32(', 'ipc70_bus.tick(', 'service_one(',
            'ctx.pc=', 'ctx.msr=', 'ctx.gpr[3]=','ctx.srr0=',
            'StmIos::Reply','StmIos::Invalid','run_game(ctx)'
        ):
            if forbidden.endswith('='):
                import re
                self.assertIsNone(re.search(r'\b'+re.escape(forbidden)+r'(?!=)',TRACE))
            else:
                self.assertNotIn(forbidden,TRACE)

    def test_fail_closed_when_prior_stage_changes(self):
        for source in (
            self.original.replace('V378_NAND_DISPATCH_ENTRY route=','lost'),
            self.original.replace('V378_NAND_DISPATCH_TRIAL handler=','lost'),
            self.original.replace('const bool v378_completed=','lost'),
            self.original.replace('++v378_dispatch_seen;','missing'),
            self.original.replace('static unsigned v378_dispatch_seen=0u;','missing'),
            self.original.replace('V377_NAND_HANDLER_TRIAL stopped=','lost'),
            patch(self.original),
        ):
            with self.assertRaises(ValueError):
                patch(source)
if __name__=='__main__':
    unittest.main()
