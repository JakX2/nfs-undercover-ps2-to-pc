#!/usr/bin/env python3
"""V340 original-free source patch tests."""
import unittest
from derive_v340_nand_mmio_probe import HEADER, INJECTION, MARKER, patch

FIXTURE=(
    "bool v250_candidate_mode=false;\n"
    "unsigned v250_nand_seen=0;\n"
    "if(v250_candidate_mode&&v250_nand_seen==1u){}\n"
    "if(v250_candidate_mode&&v250_nand_seen==1u){}\n"
    +HEADER+"\n   if(irq76_ipc&&(!v250_candidate_mode||v250_nand_seen==0u)){}\n"
)

class Tests(unittest.TestCase):
    def test_bounded_observation_is_reversible_and_read_only(self):
        result=patch(FIXTURE)
        self.assertEqual(result.count(MARKER),1)
        self.assertEqual(result.replace(HEADER+INJECTION,HEADER,1),FIXTURE)
        self.assertIn("if(v250_candidate_mode&&v250_nand_seen==1u)",INJECTION)
        self.assertIn("v340_mmio_n<16u",INJECTION)
        for category in ("PPCMSG","PPCCTRL","PI_MASK","PPC_MASK","PPC_FLAG"):
            self.assertIn(category,INJECTION)
        for old in ("irq76_ipc","submit72_active","post117_send"):
            self.assertIn(old,INJECTION)
        self.assertIn("ipc70_bus.read32(addr).has_value()",INJECTION)
        for forbidden in ("ipc70_bus.write32", "ctx.gpr", "ctx.msr=", "ctx.is_running",
                          "throw ", "mem_.write", "mmio_writes.emplace_back"):
            self.assertNotIn(forbidden,INJECTION)
        self.assertNotIn("<<addr",INJECTION)
        self.assertNotIn("<<value",INJECTION)
    def test_duplicate_or_missing_seams_fail_closed(self):
        for altered in (FIXTURE.replace(HEADER,"",1),FIXTURE+HEADER,
                        FIXTURE.replace("v250_candidate_mode","not_candidate"),
                        FIXTURE.replace("v250_nand_seen","not_seen")):
            with self.subTest(size=len(altered)):
                with self.assertRaises(ValueError):
                    patch(altered)
    def test_no_double_instrumentation(self):
        with self.assertRaises(ValueError):
            patch(patch(FIXTURE))
    def test_no_proprietary_code_in_source_fixture(self):
        self.assertNotIn("func_805",INJECTION)
        self.assertNotIn("read32(value",INJECTION)
        self.assertNotIn("private-v310",INJECTION)

if __name__=="__main__":
    unittest.main()
