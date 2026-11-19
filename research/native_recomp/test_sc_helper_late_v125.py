#!/usr/bin/env python3
"""Owner-free late V125 patch tests: exact placeholder and unchanged section geometry."""
import struct
import unittest
from extend_private_text import NOP,STUB,unpack
from restore_sc_helper_late_v125 import ENTRY,MAX_SPAN,restore,select_body,placeholder_capacity
from pathlib import Path
HERE=Path(__file__).resolve().parent

def synthetic(payload):
    raw=bytearray(256)
    struct.pack_into(">I",raw,0,256)
    struct.pack_into(">I",raw,0x48,ENTRY-0x10)
    struct.pack_into(">I",raw,0x90,len(payload))
    return bytes(raw)+payload

class LateHelper(unittest.TestCase):
    def test_exact_restore(self):
        size=0x30
        before=synthetic(NOP*4+STUB+NOP*((size-8)//4)+NOP*8)
        body=NOP*((size//4)-1)+struct.pack(">I",0x4e800020)
        after=restore(before,body)
        self.assertEqual(after[:256],before[:256])
        self.assertEqual(len(after),len(before))
        self.assertEqual(after[256:272],before[256:272])
        self.assertEqual(after[-32:],before[-32:])
        self.assertEqual(after[272:272+size],body)
        self.assertEqual(restore.__name__,"restore")
        with self.assertRaises(ValueError):
            restore(after,body)
    def test_rejects_unrelated_installed_code(self):
        size=0x30
        body=NOP*((size//4)-1)+struct.pack(">I",0x4e800020)
        data=bytearray(STUB+NOP*((size-8)//4))
        data[12:16]=b"\x00\x00\x00\x00"
        with self.assertRaises(ValueError):
            restore(synthetic(NOP*4+bytes(data)+NOP*8),body)
        with self.assertRaises(ValueError):
            restore(synthetic(NOP*4+STUB+NOP*8),body)
    def test_prefix_classifies_synthetic_and_authenticated(self):
        from restore_sc_helper_late_v125 import prefix_kind
        fake=synthetic(NOP*4+STUB+NOP*8)
        owner=synthetic(NOP*4+struct.pack(">II",0x7c0802a6,0x4e800020)+NOP*8)
        self.assertEqual(prefix_kind(fake,owner),1)
        self.assertEqual(prefix_kind(synthetic(NOP*4+NOP*2+NOP*8),owner),2)
        self.assertEqual(prefix_kind(owner,owner),3)
        self.assertEqual(prefix_kind(synthetic(NOP*4+b"\x00"*8+NOP*8),owner),4)
    def test_capacity_stops_before_restored_neighbor(self):
        body=NOP*4+STUB+NOP*14+struct.pack(">I",0x7c0802a6)+NOP*8
        fixture=synthetic(body)
        self.assertEqual(placeholder_capacity(fixture),0x40)
        with self.assertRaises(ValueError):
            placeholder_capacity(synthetic(NOP*4+NOP*2+NOP*22))
        # Exact insertion remains bounded by the next genuine instruction.
        restored=NOP*11+struct.pack(">I",0x4e800020)
        got=restore(fixture,restored)
        self.assertEqual(got[-36:],fixture[-36:])
    def test_bounded_original_terminal(self):
        body=bytearray(NOP*(MAX_SPAN//4))
        struct.pack_into(">I",body,0,0x7c0802a6)
        struct.pack_into(">I",body,0x2c,0x4e800020)
        self.assertEqual(MAX_SPAN,0x160)
        sample=synthetic(NOP*4+bytes(body))
        self.assertEqual(len(select_body(sample)),0x30)
    def test_runner_must_patch_late(self):
        import inspect
        from derive_v125_sc_helper_runner import derive
        shell=derive((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        self.assertIn('restore_sc_helper_late_v125.py',shell)
        self.assertIn('python3 "$here/make_start_to_ipc_ack_v77.py"',shell)
        self.assertNotIn('python3 "$here/make_start_to_sc_helper_v125.py"',shell)
        self.assertLess(shell.index("V104_STAGE geometry_verified"),shell.index("V125_LATE_RESTORE"))
        self.assertIn('derive_v125_sc_helper_generator.py',shell)

if __name__=="__main__":
    unittest.main()
