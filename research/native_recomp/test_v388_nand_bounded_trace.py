#!/usr/bin/env python3
"""V388 original-free regression: at most 16 authentic calls or native Y1 ACK."""
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
from derive_v387_nand_reply_route import patch as v387
from derive_v385_nand_armmsg_scope import OLD as V80_FIRST
from derive_v352_nand_mailbox_route import HEADER,INJECTION
from test_v377_nand_vector_handler import SOURCE
from derive_v388_nand_bounded_trace import patch,TRACE,ACK,RESUME,MARKER,TRIAL
class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source=SOURCE.replace('void prior(){',
            HEADER+INJECTION+'\n}\nvoid v80(){\n'+V80_FIRST+
            '\n}\nvoid prior(){',1)
        cls.prior=v387(v386(arm(v385(v384(v383(v382(v381(
            v380(v379(v378(v377(source))))))))))))
    def test_execute_real_guest_only_with_hard_function_entry_cap(self):
        out=patch(self.prior)
        self.assertEqual(out.count(MARKER),2)
        self.assertEqual(out.count(TRIAL),1)
        self.assertIn('v387_event==2u',RESUME)
        self.assertIn('c.pc==nwii::runtime::v387_next_pc',RESUME)
        self.assertIn('c.lr==nwii::runtime::v387_next_lr',RESUME)
        self.assertIn('v388_calls==16u',RESUME)
        self.assertEqual(out.count('try{run_game(c);}') ,
                         self.prior.count('try{run_game(c);}')+1)
        self.assertIn('V385_NAND_ARMMSG_MIRROR coherent=',out)
    def test_no_synthetic_reply_or_msr_guest_writes(self):
        for marker in (
            'v388_active&&v388_kind==0u',
            'ctx.inst_count>v388_start_inst',
            '++v388_calls;',
            'v388_writer=v388_writer||(addr==0x8051906cu)',
            'v388_read=v388_read||(addr==0x8051905cu)',
            'v388_cache=v388_cache||(addr==0x80522294u)',
            'ctx.is_running=false;throw ExceptionStop{};'
        ):self.assertIn(marker,TRACE)
        for marker in (
            '((*v387_prior&M::Y1)!=0u)',
            '((*now&(M::Y1|M::Y2))==0u)',
            '((*flag&H::IPC_PPC)!=0u)',
            'ipc70_bus.external_irq_level()',
            'throw ExceptionStop{};'
        ):self.assertIn(marker,ACK)
        for block in ('service_one(', 'ipc70_bus.tick(', 'ipc70_bus.write32(',
                      'ipc70_ram.write32(', 'ctx.pc=', 'ctx.msr=', 'ctx.lr='):
            if block.endswith('='):
                self.assertIsNone(re.search(r'\b'+re.escape(block)+r'(?!=)',TRACE))
            else:self.assertNotIn(block,TRACE+ACK)
    def test_fail_closed_on_prior_source_changes(self):
        for src in (
            self.prior.replace('V387_NAND_ROUTE_EVENT kind=','lost'),
            self.prior.replace('V387_NAND_ROUTE_TRIAL kind=','lost'),
            self.prior.replace('V386_NAND_NEXT_ENTRY guest=','lost'),
            self.prior.replace('V385_NAND_ARMMSG_MIRROR coherent=','lost'),
            self.prior.replace('V387 original NAND successor reached neither guest ACK nor guest call','lost'),
            patch(self.prior),
        ):
            with self.assertRaises(ValueError):patch(src)
if __name__=='__main__':unittest.main()
