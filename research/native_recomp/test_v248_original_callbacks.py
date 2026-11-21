#!/usr/bin/env python3
"""V248 original-free synthetic fixture restoration and preservation."""
import hashlib
import struct
import unittest
from audit_v245_generated_callback import SPANS
from make_osinit_execparams_v28 import text_at
from restore_v248_original_callbacks import restore,BLR
from extend_private_text import NOP

def synthetic():
    lo=min(pc for pc,n in SPANS.values())
    hi=max(pc+n for pc,n in SPANS.values())
    size=hi-lo
    a=bytearray(256+size)
    struct.pack_into(">I",a,0,256)
    struct.pack_into(">I",a,0x48,lo)
    struct.pack_into(">I",a,0x90,size)
    a[256:]=NOP*(size//4)
    # Synthetic values are not the original game instruction data.
    for k in ("cb","nand"):
        addr,n=SPANS[k]
        pos=256+addr-lo
        a[pos:pos+4]=b"\x12\x34\x56\x78"
        a[pos+n-4:pos+n]=BLR
    original=bytes(a)
    b=bytearray(a)
    for k in ("cb","nand"):
        addr,n=SPANS[k]
        pos=256+addr-lo
        b[pos:pos+n]=NOP*(n//4)
    return original,bytes(b)

class V248(unittest.TestCase):
    def test_authentic_two_span_reversal(self):
        a,b=synthetic()
        sha=hashlib.sha256(a).hexdigest()
        restored=restore(a,b,sha)
        self.assertEqual(restored,a)
        self.assertNotEqual(b,a)
        for k in SPANS:
            addr,n=SPANS[k]
            self.assertEqual(text_at(restored,addr,n),text_at(a,addr,n))

    def test_reject_wrong_sha_and_unexpected_original_bytes(self):
        a,b=synthetic()
        sha=hashlib.sha256(a).hexdigest()
        with self.assertRaises(ValueError):restore(a,b,"deadbeef")
        bad=bytearray(b)
        addr,_=SPANS["cb"]
        base=min(pc for pc,n in SPANS.values())
        bad[256+addr-base]=0x42
        with self.assertRaises(ValueError):restore(a,bytes(bad),sha)

    def test_reject_modified_isfs_or_ipc_control(self):
        a,b=synthetic()
        sha=hashlib.sha256(a).hexdigest()
        base=min(pc for pc,n in SPANS.values())
        for key in ("isfs","ipc"):
            bad=bytearray(b)
            addr,_=SPANS[key]
            bad[256+addr-base]^=1
            with self.assertRaises(ValueError):restore(a,bytes(bad),sha)

if __name__=="__main__":
    unittest.main()
