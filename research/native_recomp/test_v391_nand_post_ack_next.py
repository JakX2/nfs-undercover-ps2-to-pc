#!/usr/bin/env python3
"""V391 original-free bounded post-NAND ACK call chain tests."""
import re
import unittest
from test_v390_nand_post_ack import Tests as V390Fixture
from derive_v390_nand_post_ack import patch as v390
from derive_v391_nand_post_ack_next import patch,TRACE,MARKER,TRIAL,STOP,CONTINUE

class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        V390Fixture.setUpClass()
        cls.prior=v390(V390Fixture.prior)
    def test_bounded_real_guest_trace_preserves_both_ack_assertions(self):
        result=patch(self.prior)
        self.assertEqual(result.count(MARKER),1)
        self.assertEqual(result.count(TRIAL),1)
        self.assertNotIn(STOP,result)
        self.assertIn(CONTINUE,result)
        self.assertIn('V390_NAND_POST_ACK guest=',result)
        self.assertIn('V389_NAND_FLAG_ACK before=',result)
        self.assertIn('V388_NAND_BOUNDARY kind=1',result)
        self.assertIn('check(v390_completed,',result)
        self.assertIn('check(v391_completed,',result)
        self.assertEqual(result.count('nwii::runtime::v391_kind=0u;'),1)
        self.assertLess(result.index('nwii::runtime::v391_kind=0u;'),
                        result.index('c.is_running=true; // execute up to 16'))
    def test_callback_only_classification_no_guest_mutation(self):
        for part in (
            'v388_active&&v389_after_y1&&v389_flag_seen==1u',
            'v390_call_seen==1u&&v391_kind==0u',
            'ctx.inst_count>v391_start_inst',
            'ctx.lr>=0x805190c0u&&ctx.lr<0x80519318u',
            '((*ctl&(M::Y1|M::Y2))==0u)',
            '((*flag&H::IPC_PPC)==0u)',
            '!ipc70_bus.external_irq_level()',
            'addr==0x80522af4u||addr==0x805228ccu',
            'addr==0x804f0e04u',
            'v391_calls==16u',
            'ctx.is_running=false;throw ExceptionStop{};'
        ):self.assertIn(part,TRACE,part)
        for forbidden in (
            'service_one(', 'ipc70_bus.write32(', 'ipc70_bus.tick(',
            'ipc70_ram.write32(', 'ctx.pc=', 'ctx.lr=', 'ctx.msr=',
            'StmIos::Reply', 'StmIos::Invalid','run_game(ctx)'
        ):
            if forbidden.endswith('='):
                self.assertIsNone(re.search(r'\b'+re.escape(forbidden)+r'(?!=)',TRACE))
            else:self.assertNotIn(forbidden,TRACE)
    def test_reject_missing_prior_observer_or_reapply(self):
        for bad in (
            self.prior.replace('V390_NAND_POST_ACK guest=','absent'),
            self.prior.replace('V390_NAND_POST_ACK_TRIAL flag=','absent'),
            self.prior.replace('V389_NAND_FLAG_ACK before=','absent'),
            self.prior.replace('V385_NAND_ARMMSG_MIRROR coherent=','absent'),
            self.prior.replace(STOP,'missing'),
            self.prior.replace('V390 original NAND guest never left Hollywood ACK for next callee','absent'),
            patch(self.prior)
        ):
            with self.assertRaises(ValueError):patch(bad)
if __name__=="__main__":unittest.main()
