#!/usr/bin/env python3
"""V352 original-free NAND mailbox routing regression tests."""
from pathlib import Path
import tempfile
import unittest

from derive_v352_nand_mailbox_route import HEADER, INJECTION, MARKER, patch

FIXTURE=(
    "bool v250_candidate_mode=false;\n"
    "unsigned v250_nand_seen=0;\n"
    "void test(){ if(v250_candidate_mode&&v250_nand_seen==1u){} "
    "ipc70_bus.write32(0u,0u); ipc70_ram.valid(0u,64u);"
    "mmio_writes.emplace_back(0u,0u); }\n"
    +HEADER+"\n  if(ipc69_active){}\n"
)

class Tests(unittest.TestCase):
    def test_candidate_only_original_value_is_forwarded_without_fabrication(self):
        derived=patch(FIXTURE)
        self.assertEqual(derived.count(MARKER),2)
        self.assertEqual(derived.replace(HEADER+INJECTION,HEADER,1),FIXTURE)
        for required in (
            "v250_candidate_mode&&v250_nand_seen==1u",
            "addr==B::IPC+M::PPCMSG", "addr==B::MIRROR+M::PPCMSG",
            "addr==B::IPC+M::PPCCTRL","addr==B::MIRROR+M::PPCCTRL",
            "value!=0u&&(value&31u)==0u",
            "ipc70_ram.valid(value,64u)", "ipc70_bus.write32(addr,value)",
            "ipc70_bus.pending_native_ios_request()",
            "mmio_writes.emplace_back(addr,value)",
        ):
            self.assertIn(required,INJECTION)
        for forbidden in (
            "ipc70_bus.tick(","signal_event(","ctx.gpr[","ctx.msr=",
            "ctx.is_running=false","ipc70_ram.write",
            "IpcMailbox::ARMCTRL","StmIos::Reply","0x8051",
        ):
            self.assertNotIn(forbidden,INJECTION)
        self.assertNotIn("<<addr",INJECTION)
        self.assertNotIn("<<value",INJECTION)

    def test_unmapped_original_request_fails_closed(self):
        self.assertIn("V352 authentic NAND IPC message pointer invalid",INJECTION)
        self.assertIn('V352_NAND_BUS kind=1 mapped=0 accepted=0 queued=0',INJECTION)
        self.assertIn("check(false,",INJECTION)
        self.assertIn('check(accepted,',INJECTION)

    def test_old_request_routing_remains_unchanged(self):
        derived=patch(FIXTURE)
        self.assertIn("  if(ipc69_active){}",derived)
        self.assertEqual(derived.count("  if(ipc69_active){}"),1)
        self.assertIn("    if(message||control){",derived)
        self.assertIn("if(v250_candidate_mode&&v250_nand_seen==1u)",derived)

    def test_missing_or_ambiguous_patch_seam_rejected(self):
        for altered in (
            FIXTURE.replace(HEADER,"",1),
            FIXTURE+HEADER,
            FIXTURE.replace("v250_nand_seen","nand_not_seen"),
            FIXTURE.replace("ipc70_bus.write32","unrelated_write"),
            FIXTURE.replace("ipc70_ram.valid","unrelated_valid"),
        ):
            with self.subTest(size=len(altered)):
                with self.assertRaises(ValueError):
                    patch(altered)

    def test_no_double_instrumentation(self):
        with self.assertRaises(ValueError):
            patch(patch(FIXTURE))

    def test_no_sensitive_values_in_public_output(self):
        self.assertNotIn('std::hex',INJECTION)
        self.assertNotIn('" path="',INJECTION)
        self.assertNotIn('" phys="',INJECTION)
        self.assertNotIn('read32(value',INJECTION)

if __name__=="__main__":
    unittest.main()
