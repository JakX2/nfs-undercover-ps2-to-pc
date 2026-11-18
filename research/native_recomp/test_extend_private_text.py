#!/usr/bin/env python3
"""Synthetic fixture expansion tests; no owner content required."""
import struct
import unittest
from extend_private_text import install,unpack,NOP,STUB,MAX_EXTENSION
def fixture():
    raw=bytearray(256)
    for kind,i,base,data in ((0,0,0x80004000,NOP*4),(0,1,0x80004100,NOP*4),
                             (1,0,0x80004200,b"data")):
        for k,v in zip((0x1c,0x64,0xac) if kind else (0,0x48,0x90),(len(raw),base,len(data))):
            struct.pack_into(">I",raw,k+i*4,v)
        raw.extend(data)
    struct.pack_into(">III",raw,0xd8,0x80004300,0x100,0x80004000)
    return bytes(raw)
class ExtensionTest(unittest.TestCase):
    def test_extend(self):
        raw=fixture()
        result=install(raw,[(0x80004004,NOP*2,STUB),(0x80004030,NOP*2,STUB)])
        old=unpack(raw);new=unpack(result)
        self.assertEqual(new[0][3],NOP+STUB+NOP*9+STUB)
        self.assertEqual(old[1:],new[1:])
        self.assertEqual(raw[0xd8:256],result[0xd8:256])
    def test_reject(self):
        raw=fixture()
        for patches in ([(0x80004004,STUB,NOP*2)],[(0x800040fc,NOP*2,STUB)],
                       [(0x80004200,NOP*2,STUB)],[(0x80004300,NOP*2,STUB)],
                       [(0x80004110+MAX_EXTENSION,NOP*2,STUB)],
                       [(0x80004004,NOP*2,STUB),(0x80004008,NOP*2,STUB)]):
            with self.subTest(patches=patches),self.assertRaises(ValueError):
                install(raw,patches)
if __name__=="__main__":unittest.main()
