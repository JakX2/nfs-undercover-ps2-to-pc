#!/usr/bin/env python3
"""V389 test: original guest Y1 then distinct Hollywood flag W1C."""
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
from derive_v388_nand_bounded_trace import patch as v388
from derive_v385_nand_armmsg_scope import OLD as V80_FIRST
from derive_v352_nand_mailbox_route import HEADER,INJECTION as V352
from derive_v370_nand_ipc_flag_w1c import INJECTION as V370
from test_v377_nand_vector_handler import SOURCE
from derive_v389_nand_hollywood_ack import (
    patch,MARKER,TRIAL,Y1_END,Y1_CONTINUE,FLAG_PROOF,TRIAL_PROOF
)
class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source=SOURCE.replace('void prior(){',
            HEADER+V370+V352+'\n}\nvoid v80(){\n'+V80_FIRST+
            '\n}\nvoid prior(){',1)
        cls.prior=v388(v387(v386(arm(v385(v384(v383(v382(v381(
            v380(v379(v378(v377(source)))))))))))))
    def test_separate_original_y1_flag_and_retained_guest_instruction(self):
        out=patch(self.prior)
        self.assertEqual(out.count(MARKER),1)
        self.assertEqual(out.count(TRIAL),1)
        self.assertNotIn(Y1_END,out)
        self.assertIn(Y1_CONTINUE,out)
        self.assertIn('nwii::runtime::v389_flag_seen==1u',out)
        self.assertIn('V370_NAND_FLAG_W1C n=',out)
        self.assertIn('V388_NAND_BOUNDARY kind=1',out)
        self.assertEqual(out.count('nwii::runtime::v389_flag_seen=0u;'),1)
        self.assertLess(out.index('nwii::runtime::v389_flag_seen=0u;'),
                        out.index('c.is_running=true; // execute up to 16'))
    def test_original_flag_mmio_is_not_fabricated(self):
        for part in (
            'const bool y1clear=control.has_value()', 
            'const bool wrote=(value&H::IPC_PPC)!=0u',
            'const bool cleared=!remaining;',
            'const bool down=!ipc70_bus.external_irq_level();',
            'ipc70_ram.cpu->inst_count>v389_y1_inst',
            'ipc70_ram.cpu->is_running=false;throw ExceptionStop{};'
        ):self.assertIn(part,FLAG_PROOF)
        for forbidden in (
            'service_one(','ipc70_bus.write32(', 'ipc70_bus.tick(',
            'ipc70_ram.write32(', 'ipc70_ram.cpu->pc=',
            'ipc70_ram.cpu->lr=','StmIos::Reply'
        ):self.assertNotIn(forbidden,FLAG_PROOF)
        self.assertNotIn('ipc70_ram.cpu->is_running=false',Y1_CONTINUE)
        self.assertNotIn('throw ExceptionStop{}',Y1_CONTINUE)
        self.assertIn('v389_after_y1=true;',Y1_CONTINUE)
    def test_retained_v388_original_checkpoint_uses_later_real_stop(self):
        self.assertIn('nwii::runtime::v388_kind==1u',TRIAL_PROOF)
        self.assertIn('nwii::runtime::v389_flag_seen==1u',TRIAL_PROOF)
        self.assertIn('!nwii::runtime::ipc70_bus.external_irq_level()',TRIAL_PROOF)
        self.assertIn('check(v389_completed,',TRIAL_PROOF)
    def test_source_drift_and_duplicate_insertion_rejected(self):
        for src in (
            self.prior.replace('V388_NAND_BOUNDARY kind=','lost'),
            self.prior.replace('V388_NAND_BOUNDED_TRIAL kind=','lost'),
            self.prior.replace('V387_NAND_ROUTE_EVENT kind=','lost'),
            self.prior.replace('V385_NAND_ARMMSG_MIRROR coherent=','lost'),
            self.prior.replace('V370_NAND_FLAG_W1C n=','lost'),
            self.prior.replace('V388 original NAND bounded guest call chain yielded no verified stop','lost'),
            patch(self.prior)
        ):
            with self.assertRaises(ValueError):patch(src)
if __name__=='__main__':unittest.main()
