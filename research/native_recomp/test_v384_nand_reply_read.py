#!/usr/bin/env python3
"""V384 original-free tests of genuine NAND reply-handler PPC read."""
import re
import unittest
from derive_v377_nand_vector_handler import patch as v377
from derive_v378_nand_irq_dispatch import patch as v378
from derive_v379_nand_timebase_frontier import patch as v379
from derive_v380_nand_scheduler_frontier import patch as v380
from derive_v381_nand_ipc_handler import patch as v381
from derive_v382_nand_ipc_next import patch as v382
from derive_v383_nand_reply_handler import patch as v383
from test_v377_nand_vector_handler import SOURCE
from derive_v384_nand_reply_read import patch,TRACE,MARKER,TRIAL,STOP,CONTINUE

class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original=v383(v382(v381(v380(v379(v378(v377(SOURCE)))))))
    def test_guest_reply_handler_to_native_ppcctrl_read(self):
        output=patch(self.original)
        self.assertIn(CONTINUE,output)
        self.assertNotIn(STOP,output)
        self.assertEqual(output.count(MARKER),1)
        self.assertEqual(output.count(TRIAL),1)
        self.assertIn('c.pc==0x8051905cu',output)
        self.assertIn('nwii::runtime::v384_read_seen==1u',output)
        self.assertIn('V160 did not execute original SC Y1 exception vector to handler',output)
        self.assertEqual(output.count('nwii::runtime::v384_read_seen=0u;'),1)
        self.assertEqual(output.count('nwii::runtime::v384_reply_inst=0u;'),1)
        self.assertLess(output.index('nwii::runtime::v384_read_seen=0u;'),
                        output.index('c.is_running=true;'))
    def test_only_guest_hardware_and_verified_original_calls(self):
        for key in (
            'addr==0x8051905cu&&ctx.pc==addr',
            'ctx.lr==0x805190e8u', 'v382_next_pc==0x8051905cu',
            'ctx.mmu.read32(IRQ_TABLE+27u*4u)==0x80519318u',
            '((*ctrl&M::Y1)!=0u)','((*ctrl&M::Y2)==0u)',
            '((*flag&H::IPC_PPC)!=0u)',
            'ctx.inst_count>v384_reply_inst',
            'ctx.is_running=false;throw ExceptionStop{};'
        ):
            self.assertIn(key,TRACE,key)
        for key in ('StmIos::Reply','StmIos::Invalid','service_one(',
                    'ipc70_bus.write32(', 'ipc70_bus.tick(', 'ipc70_ram.write32(',
                    'ctx.pc=', 'ctx.msr=', 'ctx.gpr[3]=','run_game(ctx)'):
            if key.endswith('='):
                self.assertIsNone(re.search(r'\b'+re.escape(key)+r'(?!=)',TRACE))
            else:
                self.assertNotIn(key,TRACE,key)
    def test_rewrite_fails_closed_when_prior_guest_checkpoint_changes(self):
        for altered in (
            self.original.replace('V383_NAND_REPLY_ENTRY read=','lost'),
            self.original.replace('V383_NAND_REPLY_TRIAL next=','lost'),
            self.original.replace('const bool v383_completed=','lost'),
            self.original.replace('nwii::runtime::v383_read_inst=0u;','lost'),
            self.original.replace('++v383_reply_seen;','lost'),
            patch(self.original)
        ):
            with self.assertRaises(ValueError):
                patch(altered)
if __name__=='__main__':
    unittest.main()
