#!/usr/bin/env python3
"""V382 original-free IPC nested guest-call observation invariants."""
import re
import unittest
from derive_v377_nand_vector_handler import patch as v377
from derive_v378_nand_irq_dispatch import patch as v378
from derive_v379_nand_timebase_frontier import patch as v379
from derive_v380_nand_scheduler_frontier import patch as v380
from derive_v381_nand_ipc_handler import patch as v381
from test_v377_nand_vector_handler import SOURCE
from derive_v382_nand_ipc_next import patch,TRACE,MARKER,TRIAL,STOP,CONTINUE

class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prior=v381(v380(v379(v378(v377(SOURCE)))))
    def test_ipc_handler_original_next_call_not_fake(self):
        output=patch(self.prior)
        self.assertIn(CONTINUE,output)
        self.assertNotIn(STOP,output)
        self.assertEqual(output.count(MARKER),1)
        self.assertEqual(output.count(TRIAL),1)
        self.assertIn('nwii::runtime::v382_next_seen==1u',output)
        self.assertIn('c.pc==nwii::runtime::v382_next_pc',output)
        self.assertIn('V160 did not execute original SC Y1 exception vector to handler',output)
        self.assertEqual(output.count('nwii::runtime::v382_next_seen=0u;'),1)
        self.assertEqual(output.count('nwii::runtime::v382_ipc_inst=0u;'),1)
        self.assertLess(output.index('nwii::runtime::v382_next_seen=0u;'),
                        output.index('c.is_running=true;'))
    def test_classification_cannot_override_observed_guest_call(self):
        for needed in (
            'ctx.pc==addr&&ctx.lr>=0x80519318u',
            'ctx.lr<0x805194c4u&&(ctx.lr&3u)==0u',
            'ctx.mmu.read32(IRQ_TABLE+27u*4u)==0x80519318u',
            'ctx.inst_count>v382_ipc_inst',
            'addr==0x8051905cu||addr==0x8051906cu',
            'addr==0x8051b060u', 'check(guest&&registered&&masked&&advanced',
            'ctx.is_running=false;throw ExceptionStop{};'
        ):
            self.assertIn(needed,TRACE)
        for blocked in ('service_one(', 'ipc70_bus.write32(',
                        'ipc70_bus.tick(', 'ipc70_ram.write32(',
                        'ctx.pc=', 'ctx.msr=','ctx.srr0=','StmIos::Reply',
                        'StmIos::Invalid','run_game(ctx)'):
            if blocked.endswith('='):
                self.assertIsNone(re.search(r'\b'+re.escape(blocked)+r'(?!=)',TRACE))
            else:
                self.assertNotIn(blocked,TRACE)
    def test_previous_checkpoint_drift_stops_derivation(self):
        for altered in (
            self.prior.replace('V381_NAND_IPC_ENTRY registered=','lost'),
            self.prior.replace('V381_NAND_IPC_TRIAL scheduler=','lost'),
            self.prior.replace('const bool v381_completed=','lost'),
            self.prior.replace('nwii::runtime::v381_scheduler_inst=0u;','lost'),
            self.prior.replace('++v381_ipc_seen;','lost'),
            patch(self.prior)
        ):
            with self.assertRaises(ValueError):
                patch(altered)
if __name__=='__main__':
    unittest.main()
