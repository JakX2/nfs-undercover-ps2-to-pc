#!/usr/bin/env python3
"""Original-free V127 authenticated OSInit tail restoration tests."""
import struct
import unittest
from pathlib import Path
from restore_v127_osinit_tail import ENTRY,SIZE,OLD,NEXT_STUB,restore
from make_osinit_execparams_v28 import SC,BLR,NOP
HERE=Path(__file__).resolve().parent

def dol(words):
    raw=bytearray(256+len(words))
    struct.pack_into(">I",raw,0,256)
    struct.pack_into(">I",raw,0x48,ENTRY)
    struct.pack_into(">I",raw,0x90,len(words))
    raw[256:]=words
    return bytes(raw)

class V127Restore(unittest.TestCase):
    def test_authenticated_window_preserves_all_other_bytes(self):
        new=struct.pack(">IIII",0x48000001,0x28030001,0x40820004,0x48000001)
        prior=dol(OLD+NEXT_STUB+struct.pack(">I",NOP))
        after=restore(prior,new)
        self.assertEqual(after[:256],prior[:256])
        self.assertEqual(after[256:272],new)
        self.assertEqual(after[272:],prior[272:])
        self.assertEqual(len(after),len(prior))
        with self.assertRaises(ValueError):
            restore(after,new)
    def test_rejects_other_synthetic_stubs(self):
        original=dol(OLD+NEXT_STUB)
        patch=struct.pack(">IIII",0x48000001,0x28030001,0x40820004,0x48000001)
        with self.assertRaises(ValueError):
            restore(dol(OLD+struct.pack(">II",NOP,NOP)),patch)
        with self.assertRaises(ValueError):
            restore(original,patch[:12])
        bad=bytearray(original)
        bad[256:260]=struct.pack(">I",NOP)
        with self.assertRaises(ValueError):
            restore(bytes(bad),patch)
    def test_no_game_derived_instruction_bytes_in_source(self):
        source=(HERE/"restore_v127_osinit_tail.py").read_text()
        self.assertIn("hashlib.sha256(owner).hexdigest()!=ORIGINAL_SHA",source)
        self.assertIn("majors!=(18,10,16,18)",source)
        self.assertIn("link_mask!=9",source)
        self.assertNotIn("print(body)",source)
        self.assertIn("V127_OSINIT_RESTORE ok=0",source)
if __name__=="__main__":
    unittest.main()
