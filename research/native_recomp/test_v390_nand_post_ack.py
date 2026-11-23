#!/usr/bin/env python3
"""Original-free V390 post-Hollywood ACK source invariants and regression."""
import re
import unittest
from derive_v389_nand_hollywood_ack import patch as v389
from test_v389_nand_hollywood_ack import Tests as V389Fixture
from derive_v390_nand_post_ack import patch,TRACE,FLAG_STOP,FLAG_CONTINUE,TRIAL_PROOF,MARKER,TRIAL

class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        V389Fixture.setUpClass()
        cls.prior=v389(V389Fixture.prior)
    def test_no_interrupt_ack_is_replayed_or_faked(self):
        out=patch(self.prior)
        self.assertEqual(out.count(MARKER),1)
        self.assertEqual(out.count(TRIAL),1)
        self.assertIn(FLAG_CONTINUE,out)
        self.assertNotIn(FLAG_STOP,out)
        self.assertIn("V389_NAND_FLAG_ACK before=",out)
        self.assertIn("V388_NAND_BOUNDARY kind=1",out)
        self.assertIn('V370_NAND_FLAG_W1C n=',out)
        self.assertIn('nwii::runtime::v390_call_seen==1u',out)
        self.assertIn('check(v389_completed,',out)
        self.assertIn('check(v390_completed,',out)
        self.assertEqual(out.count('nwii::runtime::v390_call_seen=0u;'),1)
        self.assertLess(out.index('nwii::runtime::v390_call_seen=0u;'),
                        out.index('c.is_running=true; // execute up to 16'))
    def test_post_ack_original_guest_call_and_hardware_clear(self):
        for token in (
            'v388_active&&v389_after_y1&&v389_flag_seen==1u',
            'ctx.lr>=0x805190c0u&&ctx.lr<0x80519318u',
            'ctx.inst_count>v390_flag_inst',
            '((*control&(M::Y1|M::Y2))==0u)',
            '((*flag&H::IPC_PPC)==0u)',
            '!ipc70_bus.external_irq_level()',
            'ctx.mmu.read32(IRQ_TABLE+27u*4u)==0x80519318u',
            'addr==0x80522294u&&ctx.lr==0x80519124u',
            'addr==0x80522af4u||addr==0x805228ccu',
            'ctx.is_running=false;throw ExceptionStop{};'
        ):
            self.assertIn(token,TRACE,token)
        for forbidden in (
            'ipc70_bus.write32(', 'ipc70_bus.tick(', 'service_one(',
            'ipc70_ram.write32(', 'ctx.pc=', 'ctx.msr=', 'ctx.lr=',
            'StmIos::Reply', 'StmIos::Invalid','run_game(ctx)'
        ):
            if forbidden.endswith('='):
                self.assertIsNone(re.search(r'\b'+re.escape(forbidden)+r'(?!=)',TRACE))
            else:
                self.assertNotIn(forbidden,TRACE)
        self.assertNotIn('throw ExceptionStop{}',FLAG_CONTINUE)
        self.assertNotIn('is_running=false',FLAG_CONTINUE)
    def test_scoped_original_guest_witness_survives(self):
        self.assertIn('v389_completed&&',TRIAL_PROOF)
        self.assertIn('c.pc==nwii::runtime::v390_call_pc',TRIAL_PROOF)
        self.assertIn('c.lr==nwii::runtime::v390_call_lr',TRIAL_PROOF)
    def test_stale_prior_or_double_apply_fails_closed(self):
        for s in (
            self.prior.replace("V389_NAND_FLAG_ACK before=","missing"),
            self.prior.replace("V389_NAND_FLAG_TRIAL y1=","missing"),
            self.prior.replace("V388_NAND_BOUNDARY kind=","missing"),
            self.prior.replace("V385_NAND_ARMMSG_MIRROR coherent=","missing"),
            self.prior.replace(FLAG_STOP,"lost"),
            self.prior.replace("V389 original NAND Hollywood flag ACK did not release native IRQ","lost"),
            patch(self.prior),
        ):
            with self.assertRaises(ValueError):patch(s)
if __name__=="__main__":unittest.main()
