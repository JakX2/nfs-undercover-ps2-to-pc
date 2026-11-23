#!/usr/bin/env python3
"""V381 tests: original registered IPC handler without SC/Y2 assumptions."""
import re
import unittest
from derive_v377_nand_vector_handler import patch as v377
from derive_v378_nand_irq_dispatch import patch as v378
from derive_v379_nand_timebase_frontier import patch as v379
from derive_v380_nand_scheduler_frontier import patch as v380
from test_v377_nand_vector_handler import SOURCE
from derive_v381_nand_ipc_handler import patch,TRACE,MARKER,TRIAL,STOP,CONTINUE

class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=v380(v379(v378(v377(SOURCE))))
    def test_only_registered_original_irq_handler_is_selected(self):
        result=patch(self.source)
        self.assertEqual(result.count(MARKER),1)
        self.assertEqual(result.count(TRIAL),1)
        self.assertIn(CONTINUE,result)
        self.assertNotIn(STOP,result)
        self.assertIn('c.pc==0x80519318u',result)
        self.assertIn('nwii::runtime::v381_ipc_seen==1u',result)
        self.assertIn('V160 did not execute original SC Y1 exception vector to handler',result)
        self.assertIn('V380_NAND_SCHED_ENTRY guest=',result)
        self.assertIn('V379_NAND_TIME_ENTRY guest=',result)
        self.assertEqual(result.count('nwii::runtime::v381_ipc_seen=0u;'),1)
        self.assertEqual(result.count('nwii::runtime::v381_scheduler_inst=0u;'),1)
        self.assertLess(result.index('nwii::runtime::v381_ipc_seen=0u;'),
                        result.index('c.is_running=true;'))
    def test_irq_slot_cpu_frame_and_hardware_are_real(self):
        for key in (
            'addr==0x80519318u&&ctx.pc==addr',
            'IRQ_TABLE+27u*4u', 'ctx.mmu.read32(IRQ_TABLE+27u*4u)==addr',
            'ctx.gpr[3]==27u&&ctx.ctr==addr',
            'ctx.lr==0x80526cacu',
            'ctx.mmu.read32(frame+408u)==v377_resume',
            'ctx.mmu.read32(frame+412u)==v377_srr1',
            'ctx.mmu.read32(frame+132u)==v377_lr',
            'ctx.mmu.read32(frame+136u)==v377_ctr',
            'ctx.mmu.read32(frame+140u)==v377_xer',
            '((*ctrl&M::Y1)!=0u)', '((*ctrl&M::Y2)==0u)',
            '((*flag&H::IPC_PPC)!=0u)',
            'ctx.inst_count>v381_scheduler_inst',
            'ctx.is_running=false;throw ExceptionStop{};'
        ):
            self.assertIn(key,TRACE,key)
        for key in (
            'StmIos::Reply','StmIos::Invalid','ipc70_ram.write32(',
            'ipc70_bus.tick(', 'ipc70_bus.write32(', 'service_one(',
            'ctx.pc=', 'ctx.msr=', 'ctx.gpr[3]=','ctx.srr0=','run_game(ctx)'
        ):
            if key.endswith('='):
                self.assertIsNone(re.search(r'\b'+re.escape(key)+r'(?!=)',TRACE))
            else:
                self.assertNotIn(key,TRACE,key)
    def test_nonunique_stale_and_changed_source_fail_closed(self):
        for changed in (
            self.source.replace('V380_NAND_SCHED_ENTRY guest=','lost'),
            self.source.replace('V380_NAND_SCHED_TRIAL time=','lost'),
            self.source.replace('const bool v380_completed=','lost'),
            self.source.replace('nwii::runtime::v380_time_inst=0u;','lost'),
            self.source.replace('++v380_scheduler_seen;','missing'),
            self.source.replace('V160 did not execute original SC Y1 exception vector to handler','lost'),
            patch(self.source)
        ):
            with self.assertRaises(ValueError):
                patch(changed)
if __name__=='__main__':
    unittest.main()
