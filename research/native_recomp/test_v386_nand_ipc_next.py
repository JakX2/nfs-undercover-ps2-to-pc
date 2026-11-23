#!/usr/bin/env python3
"""V386 original-free regression for validated NAND second IPC read resume."""
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
from derive_v385_nand_second_read import patch as v385
from test_v377_nand_vector_handler import SOURCE
from derive_v386_nand_ipc_next import patch,TRACE,RESUME,MARKER,TRIAL

class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=v385(v384(v383(v382(v381(v380(v379(v378(v377(SOURCE)))))))))
    def test_resume_v385_original_guest_call_without_writing_cpu_pc(self):
        out=patch(self.source)
        self.assertEqual(out.count(MARKER),1)
        self.assertEqual(out.count(TRIAL),1)
        self.assertIn('c.pc==0x8051905cu&&c.lr==0x805190fcu',out)
        self.assertIn('c.is_running=true; // resume original PPC function',out)
        self.assertEqual(out.count('try{run_game(c);}') ,self.source.count('try{run_game(c);}')+1)
        self.assertIn('v386_next_seen==1u',out)
        self.assertIn('v386_active=false;',out)
        self.assertIn('V160 did not execute original SC Y1 exception vector to handler',out)
        self.assertIn('V385 original NAND IpcReplyHandler second reader not entered',out)
    def test_original_linked_guest_helper_and_hardware_only(self):
        for k in (
            'addr>=0x80400000u&&addr<0x80600000u',
            'ctx.lr>=0x805190c0u&&ctx.lr<0x80519318u',
            'ctx.inst_count>v386_start_inst',
            'ctx.mmu.read32(IRQ_TABLE+27u*4u)==0x80519318u',
            'addr==0x8051906cu&&ctx.lr==0x8051910cu',
            '((*ctrl&M::Y1)!=0u)', '((*ctrl&M::Y2)==0u)',
            '((*flag&H::IPC_PPC)!=0u)',
            'ctx.is_running=false;throw ExceptionStop{};'
        ):
            self.assertIn(k,TRACE,k)
        for k in ('service_one(', 'ipc70_bus.tick(', 'ipc70_bus.write32(',
                  'ipc70_ram.write32(', 'StmIos::Reply','StmIos::Invalid',
                  'ctx.pc=', 'ctx.msr=', 'ctx.gpr[3]=','run_game(ctx)'):
            if k.endswith('='):
                self.assertIsNone(re.search(r'\b'+re.escape(k)+r'(?!=)',TRACE))
            else:self.assertNotIn(k,TRACE,k)
    def test_fail_closed_on_missing_predecessor(self):
        for bad in (
            self.source.replace('const bool v385_completed=','lost'),
            self.source.replace('V385_NAND_SECOND_READ caller=','lost'),
            self.source.replace('V385_NAND_SECOND_READ_TRIAL first=','lost'),
            self.source.replace('"V385 original NAND IpcReplyHandler second reader not entered");','lost'),
            self.source.replace('V160 did not execute original SC Y1 exception vector to handler','lost'),
            patch(self.source)
        ):
            with self.assertRaises(ValueError):patch(bad)
if __name__=='__main__':
    unittest.main()
