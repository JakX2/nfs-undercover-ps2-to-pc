#!/usr/bin/env python3
"""V128 original-free synthetic tests for bounded next-function audit."""
import struct
import unittest
from pathlib import Path
from extend_private_text import STUB,NOP
from make_osinit_execparams_v28 import BLR
from diagnose_v128_next_function import ENTRY,NEXT_KNOWN,MAX_SPAN,probe,report
HERE=Path(__file__).resolve().parent

def dol(payload:bytes)->bytes:
    raw=bytearray(256+len(payload))
    struct.pack_into(">I",raw,0,256)
    struct.pack_into(">I",raw,0x48,ENTRY)
    struct.pack_into(">I",raw,0x90,len(payload))
    raw[256:]=payload
    return bytes(raw)

class V128(unittest.TestCase):
    def test_stub_and_bounded_return(self):
        owner=bytearray(NOP*(MAX_SPAN//4))
        owner[:4]=struct.pack(">I",0x9421fff0)
        owner[28:32]=struct.pack(">I",BLR)
        private=STUB+NOP*((MAX_SPAN-8)//4)
        got=probe(dol(bytes(owner)),dol(private))
        self.assertEqual(NEXT_KNOWN-ENTRY,0x11c)
        self.assertEqual(got["prefix"],1)
        self.assertEqual(got["capacity"],MAX_SPAN//4)
        self.assertEqual(got["returns"],1)
        self.assertEqual(got["first_end"],8)
        self.assertEqual(got["eligible_first"],1)
        self.assertEqual(got["eligible_last"],1)
        self.assertIn("V128_NEXT_PROBE mapped=1 prefix=1",report(got))
    def test_nop_and_neighbor_guard(self):
        owner=bytearray(NOP*(MAX_SPAN//4))
        owner[:4]=struct.pack(">I",0x9421fff0)
        owner[44:48]=struct.pack(">I",BLR)
        fixture=NOP*4+struct.pack(">I",0x7c0802a6)+NOP*((MAX_SPAN-20)//4)
        got=probe(dol(bytes(owner)),dol(fixture))
        self.assertEqual(got["prefix"],2)
        self.assertEqual(got["capacity"],4)
        self.assertEqual(got["eligible_first"],0)
        self.assertEqual(got["eligible_last"],0)
        self.assertEqual(got["major0"],0x9421fff0>>26)
    def test_original_free_output(self):
        s=(HERE/"diagnose_v128_next_function.py").read_text()
        self.assertIn("hashlib.sha256(raw).hexdigest()!=ORIGINAL_SHA",s)
        self.assertIn("target(word,CALLSITE,True)!=ENTRY",s)
        self.assertNotIn("print(original)",s)
        self.assertNotIn("print(raw)",s)
        self.assertIn("V128_NEXT_PROBE result=failed",s)
if __name__=="__main__":
    unittest.main()
