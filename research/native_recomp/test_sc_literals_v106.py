#!/usr/bin/env python3
"""Original-free DOL initialized-data inventory tests."""
import struct
import unittest
from probe_sc_literals_v106 import PUBLIC,counts,data_sections

def fake(*payloads):
    out=bytearray(256)
    for i,payload in enumerate(payloads):
        addr=len(out)
        struct.pack_into(">I",out,0x1c+4*i,addr)
        struct.pack_into(">I",out,0x64+4*i,0x80500000+0x100*i)
        struct.pack_into(">I",out,0xac+4*i,len(payload))
        out.extend(payload)
    return bytes(out)

class ProbeSC(unittest.TestCase):
    def test_public_only(self):
        name=PUBLIC[0][1]
        blob=fake(b"X"+name+b"Y"+name,b"/dev/fs\0",b"/dev/es\0")
        self.assertEqual(counts(blob),(2,2,0,1,1))
        self.assertEqual(len(tuple(data_sections(blob))),3)
    def test_section_boundary(self):
        word=PUBLIC[0][1]
        self.assertEqual(counts(fake(word[:8],word[8:])),(0,0,0,0,0))
    def test_reject_bad_section(self):
        blob=bytearray(fake(b"SYSCONF\0"))
        struct.pack_into(">I",blob,0x1c,0x20)
        with self.assertRaises(ValueError):counts(bytes(blob))
    def test_reject_overlap(self):
        blob=bytearray(fake(b"SYSCONF\0",b"/dev/fs\0"))
        struct.pack_into(">I",blob,0x1c+4,0x100)
        with self.assertRaises(ValueError):counts(bytes(blob))

if __name__=="__main__":
    unittest.main()
