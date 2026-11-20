#!/usr/bin/env python3
"""Original-free conditional PPC branch decoder and OSInit retry tests."""
import unittest
from pathlib import Path
from diagnose_v131_osinit_retry import CALL,CONDITION,EXPECTED_CALLEE,branch16_dest,analyze,report
HERE=Path(__file__).resolve().parent

class V131Decode(unittest.TestCase):
    def test_signed_relative_branch(self):
        negative=(16<<26)|(12<<21)|(2<<16)|(0xfff8&0xfffc)
        self.assertEqual(branch16_dest(negative,CONDITION),CONDITION-8)
        with self.assertRaises(ValueError):
            branch16_dest(0x48000001,CONDITION)
    def test_loop_compare_and_branch_without_owner_words(self):
        rel=(EXPECTED_CALLEE-CALL)&0x03fffffc
        first=(18<<26)|rel|1
        compare=(10<<26)|(3<<16)
        retry_disp=(CALL-CONDITION)&0xffff
        conditional=(16<<26)|(12<<21)|(2<<16)|(retry_disp&0xfffc)
        final=(18<<26)|(((0x805293B0-(CALL+12))&0x03fffffc))|1
        d=analyze((first,compare,conditional,final))
        self.assertEqual(d["cmp_reg"],3)
        self.assertEqual(d["compare_zero"],1)
        self.assertEqual(d["retry_back"],1)
        self.assertEqual(d["retry_on_equal"],1)
        self.assertEqual(d["next_call"],0x805293B0)
        self.assertIn("V131_OSINIT_RETRY cmp_reg=3",report(d))
    def test_private_authentication_and_no_opcode_dump(self):
        s=(HERE/"diagnose_v131_osinit_retry.py").read_text()
        self.assertIn("hashlib.sha256(raw).hexdigest()!=ORIGINAL_SHA",s)
        self.assertNotIn("print(words)",s)
        self.assertNotIn("print(raw)",s)
        self.assertIn("V131_OSINIT_RETRY result=failed",s)
if __name__=="__main__":
    unittest.main()
