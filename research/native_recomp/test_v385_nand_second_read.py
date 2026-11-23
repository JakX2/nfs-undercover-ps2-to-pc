#!/usr/bin/env python3
"""V385 original-free second IPC reader real NAND guest provenance tests."""
import re
import unittest
from derive_v377_nand_vector_handler import patch as v377
from derive_v378_nand_irq_dispatch import patch as v378
from derive_v379_nand_timebase_frontier import patch as v379
from derive_v380_nand_scheduler_frontier import patch as v380
from derive_v381_nand_ipc_handler import patch as v381
from derive_v382_nand_ipc_next import patch as v382
from derive_v383_nand_reply_handler import patch as v383
from derive_v384_nand_reply_read import patch as v384
from test_v377_nand_vector_handler import SOURCE
from derive_v385_nand_second_read import patch,TRACE,MARKER,TRIAL,STOP,CONTINUE

class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prior=v384(v383(v382(v381(v380(v379(v378(v377(SOURCE))))))))
    def test_same_guest_reader_different_original_caller(self):
        s=patch(self.prior)
        self.assertIn(CONTINUE,s)
        self.assertNotIn(STOP,s)
        self.assertEqual(s.count(MARKER),1)
        self.assertEqual(s.count(TRIAL),1)
        self.assertIn('ctx.lr==0x805190fcu',s)
        self.assertIn('nwii::runtime::v385_second_seen==1u',s)
        self.assertIn('V160 did not execute original SC Y1 exception vector to handler',s)
        self.assertEqual(s.count('nwii::runtime::v385_second_seen=0u;'),1)
        self.assertEqual(s.count('nwii::runtime::v385_first_read_inst=0u;'),1)
        self.assertLess(s.index('nwii::runtime::v385_second_seen=0u;'),
                        s.index('c.is_running=true;'))
    def test_genuine_hardware_and_guest_abi_only(self):
        for key in (
            'addr==0x8051905cu&&ctx.pc==addr&&ctx.lr==0x805190fcu',
            'ctx.mmu.read32(IRQ_TABLE+27u*4u)==0x80519318u',
            '((*ctrl&M::Y1)!=0u)', '((*ctrl&M::Y2)==0u)',
            '((*flag&H::IPC_PPC)!=0u)',
            'ctx.inst_count>v385_first_read_inst',
            'ctx.is_running=false;throw ExceptionStop{};'
        ):
            self.assertIn(key,TRACE)
        for key in ('StmIos::Reply','StmIos::Invalid','service_one(',
                    'ipc70_bus.write32(', 'ipc70_bus.tick(', 'ipc70_ram.write32(',
                    'ctx.pc=', 'ctx.msr=', 'ctx.gpr[3]=','run_game(ctx)'):
            if key.endswith('='):
                self.assertIsNone(re.search(r'\b'+re.escape(key)+r'(?!=)',TRACE))
            else:
                self.assertNotIn(key,TRACE,key)
    def test_source_mismatch_and_reentry_fail_closed(self):
        for source in (
            self.prior.replace('V384_NAND_REPLY_READ caller=','lost'),
            self.prior.replace('V384_NAND_REPLY_READ_TRIAL reply=','lost'),
            self.prior.replace('const bool v384_completed=','lost'),
            self.prior.replace('nwii::runtime::v384_reply_inst=0u;','lost'),
            self.prior.replace('++v384_read_seen;','lost'),
            patch(self.prior)
        ):
            with self.assertRaises(ValueError):
                patch(source)
if __name__=='__main__':
    unittest.main()
