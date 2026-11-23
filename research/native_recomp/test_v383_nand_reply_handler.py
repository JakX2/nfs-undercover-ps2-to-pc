#!/usr/bin/env python3
"""V383 original-free NAND guest IPC read to genuine reply-handler tests."""
import re
import unittest
from derive_v377_nand_vector_handler import patch as v377
from derive_v378_nand_irq_dispatch import patch as v378
from derive_v379_nand_timebase_frontier import patch as v379
from derive_v380_nand_scheduler_frontier import patch as v380
from derive_v381_nand_ipc_handler import patch as v381
from derive_v382_nand_ipc_next import patch as v382
from test_v377_nand_vector_handler import SOURCE
from derive_v383_nand_reply_handler import patch,TRACE,STOP,CONTINUE,MARKER,TRIAL

class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prior=v382(v381(v380(v379(v378(v377(SOURCE))))))
    def test_original_ipc_read_reaches_reply_handler(self):
        out=patch(self.prior)
        self.assertIn(CONTINUE,out)
        self.assertNotIn(STOP,out)
        self.assertEqual(out.count(MARKER),1)
        self.assertEqual(out.count(TRIAL),1)
        self.assertIn('c.pc==0x805190c0u',out)
        self.assertIn('nwii::runtime::v383_reply_seen==1u',out)
        self.assertIn('V160 did not execute original SC Y1 exception vector to handler',out)
        self.assertEqual(out.count('nwii::runtime::v383_reply_seen=0u;'),1)
        self.assertEqual(out.count('nwii::runtime::v383_read_inst=0u;'),1)
        self.assertLess(out.index('nwii::runtime::v383_reply_seen=0u;'),
                        out.index('c.is_running=true;'))
    def test_original_hardware_and_callsites_only(self):
        for key in (
            'addr==0x805190c0u&&ctx.pc==addr',
            'v382_next_pc==0x8051905cu',
            'ctx.lr==0x80519354u',
            'ctx.mmu.read32(IRQ_TABLE+27u*4u)==0x80519318u',
            '((*ctrl&M::Y1)!=0u)', '((*ctrl&M::Y2)==0u)',
            '((*flag&H::IPC_PPC)!=0u)',
            'ctx.inst_count>v383_read_inst',
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
    def test_changed_predecessor_and_double_application_fail(self):
        for source in (
            self.prior.replace('V382_NAND_IPC_NEXT guest=','lost'),
            self.prior.replace('V382_NAND_IPC_TRIAL ipc=','lost'),
            self.prior.replace('const bool v382_completed=','lost'),
            self.prior.replace('nwii::runtime::v382_next_pc=0u;','lost'),
            self.prior.replace('++v382_next_seen;','lost'),
            patch(self.prior)
        ):
            with self.assertRaises(ValueError):
                patch(source)
if __name__=='__main__':
    unittest.main()
