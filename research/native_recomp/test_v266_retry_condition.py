#!/usr/bin/env python3
"""V266 synthetic PowerPC immediate-compare and retry-edge proof tests."""
import unittest
from pathlib import Path
from ppc_retry_condition import classify_condition, sanitized
from audit_v266_retry_condition import inspect

CALL=0x100c

def bc(pc:int,target:int,bo:int=12,bi:int=2):
    delta=target-pc
    assert delta%4==0 and -32768<=delta<32768
    return (16<<26)|(bo<<21)|(bi<<16)|(delta&0xfffc)

def cmpwi(ra:int,imm:int,bf:int=0):
    return (11<<26)|(bf<<23)|(ra<<16)|(imm&0xffff)

def fixture(producer:int=None):
    words=[0x60000000]*18
    # CALL is at 0x100c, backedge at CALL+8.
    words[(CALL-0x1000)//4]=0x48000101
    words[(CALL+4-0x1000)//4]=cmpwi(3,0) if producer is None else producer
    words[(CALL+8-0x1000)//4]=bc(CALL+8,CALL)
    return words

class Tests(unittest.TestCase):
    def test_helper_result_zero_branch(self):
        result=classify_condition(0x1000,fixture(),CALL)
        self.assertEqual(result["producer_kind"],1)
        self.assertEqual(result["producer_cr_field"],0)
        self.assertEqual(result["producer_ra"],3)
        self.assertEqual(result["producer_imm_zero"],1)
        self.assertEqual(result["producer_imm_class"],0)
        self.assertEqual(result["compares_helper_r3"],1)
        self.assertEqual(result["backedge_from"],8)
        self.assertEqual(result["backedge_to"],0)
        self.assertIn("producer_kind=1",sanitized(result))

    def test_different_source_and_literal(self):
        result=classify_condition(0x1000,fixture(cmpwi(7,3)),CALL)
        self.assertEqual(result["producer_ra"],7)
        self.assertEqual(result["producer_imm_zero"],0)
        self.assertEqual(result["producer_imm_class"],3)
        self.assertEqual(result["compares_helper_r3"],0)
        result=classify_condition(0x1000,fixture((10<<26)|(3<<16)|2),CALL)
        self.assertEqual(result["producer_kind"],2)  # cmplwi r3, 2
        self.assertEqual(result["producer_imm_zero"],0)
        self.assertEqual(result["producer_imm_class"],2)
        self.assertEqual(result["compares_helper_r3"],1)
        result=classify_condition(0x1000,fixture(0x60000000),CALL)
        self.assertEqual(result["producer_kind"],0)
        self.assertEqual(result["producer_ra"],-1)
        self.assertEqual(result["compares_helper_r3"],0)

    def test_reject_unverified_or_multiple_backedge(self):
        words=fixture()
        words[(CALL+8-0x1000)//4]=bc(CALL+8,CALL,4,2)
        with self.assertRaisesRegex(ValueError,"unverified_edge"):
            classify_condition(0x1000,words,CALL)
        words=fixture()
        words[(CALL+12-0x1000)//4]=bc(CALL+12,CALL)
        with self.assertRaisesRegex(ValueError,"ambiguous_backedge"):
            classify_condition(0x1000,words,CALL)
        with self.assertRaises(ValueError):
            inspect(b"not an authenticated owner ELF")

    def test_ci_keeps_original_private(self):
        wf=(Path(__file__).resolve().parents[2]/
            ".github/workflows/wii-v266-retry-condition.yml").read_text(encoding="utf-8")
        self.assertIn("V266_CONDITION_AUDIT verified=1",wf)
        self.assertIn("WII_ORIGINAL_ELF_ID",wf)
        self.assertNotIn("upload-artifact",wf)
        self.assertIn("rm -rf --",wf)

if __name__=="__main__":
    unittest.main()
