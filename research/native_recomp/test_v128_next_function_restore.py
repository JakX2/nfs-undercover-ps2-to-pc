#!/usr/bin/env python3
"""V128 original-free 71-instruction restoration and overwrite guards."""
import struct
import unittest
from pathlib import Path
from make_osinit_execparams_v28 import BLR,NOP
from extend_private_text import STUB
from restore_v128_next_function import ENTRY,END,SIZE,EMPTY,verify_body,restore
HERE=Path(__file__).resolve().parent

def dol(blob:bytes)->bytes:
    raw=bytearray(256+len(blob))
    struct.pack_into(">I",raw,0,256)
    struct.pack_into(">I",raw,0x48,ENTRY)
    struct.pack_into(">I",raw,0x90,len(blob))
    raw[256:]=blob
    return bytes(raw)
def body()->bytes:
    return struct.pack(">I",0x9421fff0)+struct.pack(">I",NOP)*((SIZE//4)-2)+struct.pack(">I",BLR)

class V128Restore(unittest.TestCase):
    def test_restore_exact_original_span(self):
        self.assertEqual(SIZE,0x11c)
        before=dol(EMPTY+STUB)
        after=restore(before,body())
        self.assertEqual(after[:256],before[:256])
        self.assertEqual(after[256:256+SIZE],body())
        self.assertEqual(after[256+SIZE:],before[256+SIZE:])
        self.assertEqual(len(after),len(before))
        with self.assertRaises(ValueError):
            restore(after,body())
    def test_no_overwrite_of_other_functions(self):
        invalid=bytearray(EMPTY+STUB)
        invalid[SIZE-4:SIZE]=struct.pack(">I",0x7c0802a6)
        with self.assertRaises(ValueError):
            restore(dol(bytes(invalid)),body())
        with self.assertRaises(ValueError):
            verify_body(body()[:-4])
        mutated=body()[:-4]+struct.pack(">I",NOP)
        with self.assertRaises(ValueError):
            verify_body(mutated)
    def test_sha_and_call_edge_must_be_authenticated(self):
        source=(HERE/"restore_v128_next_function.py").read_text()
        self.assertIn("hashlib.sha256(owner).hexdigest()!=ORIGINAL_SHA",source)
        self.assertIn("target(instruction,CALLSITE,True)!=ENTRY",source)
        self.assertIn("V128_ORIGINAL_RESTORE ok=0",source)
        self.assertNotIn("print(body)",source)
if __name__=="__main__":
    unittest.main()
