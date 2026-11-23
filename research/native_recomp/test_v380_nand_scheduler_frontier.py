#!/usr/bin/env python3
"""V380 original-free source invariants for NAND Y1 OS scheduler call."""
import unittest
import re
from derive_v377_nand_vector_handler import patch as v377
from derive_v378_nand_irq_dispatch import patch as v378
from derive_v379_nand_timebase_frontier import patch as v379
from test_v377_nand_vector_handler import SOURCE
from derive_v380_nand_scheduler_frontier import (
    patch,TRACE,MARKER,TRIAL,OLD_STOP,NEW_STOP
)

class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prior=v379(v378(v377(SOURCE)))
    def test_guest_osgettime_to_scheduler(self):
        next=patch(self.prior)
        self.assertEqual(next.count(MARKER),1)
        self.assertEqual(next.count(TRIAL),1)
        self.assertEqual(next.count(NEW_STOP),1)
        self.assertNotIn(OLD_STOP,next)
        self.assertIn('c.pc==0x805293f8u',next)
        self.assertIn('V160 did not execute original SC Y1 exception vector to handler',next)
        self.assertIn('V379_NAND_TIME_ENTRY guest=',next)
        self.assertIn('V378_NAND_DISPATCH_ENTRY route=',next)
        self.assertIn('nwii::runtime::v380_scheduler_seen==1u',next)
        self.assertEqual(next.count('nwii::runtime::v380_scheduler_seen=0u;'),1)
        self.assertEqual(next.count('nwii::runtime::v380_time_inst=0u;'),1)
        self.assertLess(next.index('nwii::runtime::v380_scheduler_seen=0u;'),
                        next.index('c.is_running=true;'))
    def test_real_guest_and_hardware_only(self):
        for item in (
            'addr==0x805293f8u','ctx.pc==addr',
            'ctx.lr==0x80526c98u','ctx.inst_count>v380_time_inst',
            'ipc70_bus.external_irq_level()', '((*ctl&M::Y1)!=0u)',
            '((*ctl&M::Y2)==0u)', '((*flag&H::IPC_PPC)!=0u)',
            'ctx.is_running=false;throw ExceptionStop{};'
        ):
            self.assertIn(item,TRACE)
        for blocked in ('ipc70_bus.write32(', 'ipc70_bus.tick(', 'service_one(',
                        'ctx.gpr[3]=', 'ctx.pc=', 'ctx.msr=', 'ctx.lr=',
                        'StmIos::Reply', 'StmIos::Invalid','run_game(ctx)'):
            if blocked.endswith('='):
                self.assertIsNone(re.search(r'\b'+re.escape(blocked)+r'(?!=)',TRACE))
            else:
                self.assertNotIn(blocked,TRACE)
    def test_fails_closed_on_changed_or_repeated_staging(self):
        for s in (
            self.prior.replace('V379_NAND_TIME_ENTRY guest=','wrong'),
            self.prior.replace('V379_NAND_TIME_TRIAL dispatch=','wrong'),
            self.prior.replace('const bool v379_completed=','wrong'),
            self.prior.replace('nwii::runtime::v379_dispatch_inst=0u;','wrong'),
            self.prior.replace('V378_NAND_DISPATCH_ENTRY route=','wrong'),
            self.prior.replace('++v379_time_seen;','missing'),
            patch(self.prior),
        ):
            with self.assertRaises(ValueError):
                patch(s)
if __name__=='__main__':
    unittest.main()
