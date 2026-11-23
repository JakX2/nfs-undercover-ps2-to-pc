#!/usr/bin/env python3
"""V369 original-free post-ACK MMIO observation constraints."""
import unittest
from derive_v369_post_ack_mmio_probe import HEAD,PRIOR,MARKER,INJECTION,patch

FIXTURE=(
    "bool v250_candidate_mode=false;\n"
    "unsigned v250_nand_seen=0u;\n"
    "bool ipc69_active=false;\n"
    "bool v369_fixture(){return v250_candidate_mode&&v250_nand_seen==1u;}\n"
    "void other(){(void)ipc70_bus.services().queued_replies();}\n"
    +HEAD+"\n"
    ' std::cout<<"V367_NAND_IRQ_MASK n="<<1u;\n'
    ' check(false,"unexpected IPC mask MMIO write");\n'
    "}\n"
)

class Tests(unittest.TestCase):
    def test_only_post_ack_requests_are_classified_without_side_effects(self):
        output=patch(FIXTURE)
        self.assertEqual(output.count(MARKER),1)
        self.assertEqual(output.replace(HEAD+INJECTION,HEAD,1),FIXTURE)
        for needed in (
            "v250_candidate_mode&&v250_nand_seen==1u",
            "ipc70_bus.services().queued_replies()>0u",
            "!ipc70_bus.pending_native_ios_request()",
            "v369_count<32u",
            "addr==B::PI_MASK",
            "addr==B::IPC+H::PPC_MASK",
            "addr==B::MIRROR+H::PPC_MASK",
            "addr==B::IPC+H::PPC_FLAG",
            "addr==B::IPC+M::PPCCTRL",
            "addr==B::IPC+M::PPCMSG",
            "ipc70_bus.read32(addr).has_value()",
            "unsigned(ipc69_active)",
        ):
            self.assertIn(needed,INJECTION)
        for forbidden in (
            "ipc70_bus.write32", "service_one(", "ipc70_bus.tick(",
            "enter_external_irq(", "ctx.gpr[", "ctx.msr=", "ctx.pc=",
            "ipc70_ram.write", "ctx.is_running", "std::hex",
            "<<addr", "<<value", "StmIos::Reply",
        ):
            self.assertNotIn(forbidden,INJECTION)

    def test_candidate_phase_and_actual_native_ack_required(self):
        self.assertIn("if(v250_candidate_mode&&v250_nand_seen==1u&&",INJECTION)
        self.assertIn("queued_replies()>0u",INJECTION)
        for candidate in (False,True):
            for nand in (False,True):
                for queued in (False,True):
                    for pending in (False,True):
                        eligible=candidate and nand and queued and not pending
                        self.assertEqual(eligible,all((candidate,nand,queued,not pending)))

    def test_missing_or_ambiguous_original_seams_rejected(self):
        for broken in (
            FIXTURE.replace(HEAD,"",1),
            FIXTURE+HEAD,
            FIXTURE.replace(PRIOR,"old_mask_label",1),
            FIXTURE.replace("v250_candidate_mode","missing_candidate"),
            FIXTURE.replace("ipc70_bus.services().queued_replies()","no_native_queuing"),
            FIXTURE.replace("unexpected IPC mask MMIO write","changed legacy label"),
            patch(FIXTURE),
        ):
            with self.subTest(size=len(broken)):
                with self.assertRaises(ValueError):
                    patch(broken)

if __name__=="__main__":
    unittest.main()
