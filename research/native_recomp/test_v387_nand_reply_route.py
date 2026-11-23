#!/usr/bin/env python3
"""V387 verify no synthetic ACK, accept either authentic successor event."""
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
from derive_v385_nand_armmsg_scope import patch as arm
from derive_v386_nand_ipc_next import patch as v386
from derive_v385_nand_armmsg_scope import OLD as V80_FIRST
from derive_v352_nand_mailbox_route import HEADER,INJECTION
from test_v377_nand_vector_handler import SOURCE
from derive_v387_nand_reply_route import (
    patch,RESUME,TRACE,MMIO_END_NEW,MARKER,TRIAL
)
class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        original=SOURCE.replace('void prior(){',
            HEADER+INJECTION+'\n}\nvoid v80(){\n'+V80_FIRST+
            '\n}\nvoid prior(){',1)
        cls.prior=v386(arm(v385(v384(v383(v382(v381(
            v380(v379(v378(v377(original))))))))))
    def test_original_guest_resumed_at_saved_pc(self):
        out=patch(self.prior)
        self.assertEqual(out.count(MARKER),2)
        self.assertEqual(out.count(TRIAL),1)
        self.assertIn('c.pc==nwii::runtime::v386_next_pc',RESUME)
        self.assertIn('c.lr==nwii::runtime::v386_next_lr',RESUME)
        self.assertIn('c.is_running=true; // resume authentic original guest successor',RESUME)
        self.assertIn('nwii::runtime::v387_event==1u',RESUME)
        self.assertIn('nwii::runtime::v387_event==2u',RESUME)
        self.assertIn('V385_NAND_ARMMSG_MIRROR coherent=',out)
        self.assertEqual(out.count('try{run_game(c);}') ,
                         self.prior.count('try{run_game(c);}')+1)
    def test_original_guest_y1_w1c_hardware_validation(self):
        for expected in (
            '((*v387_prior&M::Y1)!=0u)',
            '((*after&(M::Y1|M::Y2))==0u)',
            '((*flag&H::IPC_PPC)!=0u)',
            'ipc70_bus.external_irq_level()',
            'ipc70_ram.cpu->inst_count>v387_start_inst',
            'throw ExceptionStop{};'
        ):
            self.assertIn(expected,MMIO_END_NEW,expected)
        for bad in ('service_one(','ipc70_bus.write32(',
                    'ipc70_bus.tick(','ipc70_ram.write32(',
                    'ipc70_ram.cpu->pc='):
            self.assertNotIn(bad,MMIO_END_NEW,bad)
    def test_next_guest_call_not_writer_only(self):
        for expected in (
            'ctx.inst_count>v387_start_inst',
            'ctx.lr>=0x805190c0u&&ctx.lr<0x80519318u',
            'ctx.mmu.read32(IRQ_TABLE+27u*4u)==0x80519318u',
            'addr==0x8051906cu',
            'v387_event=2u;',
            'ctx.is_running=false;throw ExceptionStop{};'
        ):
            self.assertIn(expected,TRACE,expected)
        for bad in ('ipc70_bus.tick(', 'service_one(', 'ipc70_bus.write32(',
                    'ctx.pc=', 'ctx.msr=', 'ctx.lr='):
            if bad.endswith('='):
                self.assertIsNone(re.search(r'\b'+re.escape(bad)+r'(?!=)',TRACE))
            else:self.assertNotIn(bad,TRACE)
    def test_inherited_source_drift_and_double_patch_rejected(self):
        for src in (
            self.prior.replace('V386_NAND_NEXT_ENTRY guest=','lost'),
            self.prior.replace('V386_NAND_NEXT_TRIAL stopped=','lost'),
            self.prior.replace('V385_NAND_ARMMSG_MIRROR coherent=','lost'),
            self.prior.replace('V352_NAND_BUS kind=','lost'),
            self.prior.replace('V386 original NAND reply handler failed to call next guest helper','lost'),
            patch(self.prior),
        ):
            with self.assertRaises(ValueError):patch(src)
if __name__=='__main__':unittest.main()
