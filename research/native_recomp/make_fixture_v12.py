#!/usr/bin/env python3
"""Generate a tiny synthetic Wii DOL with a legitimate BSS/data overlap."""
import struct
import sys
from pathlib import Path


def fixture():
    data = bytearray(0x118)
    for offset, value in ((0x00,0x100),(0x48,0x80004000),(0x90,16),
                          (0x1c,0x110),(0x64,0x80006000),(0xac,8),
                          (0xd8,0x80005ff0),(0xdc,0x20),(0xe0,0x80004000)):
        struct.pack_into('>I',data,offset,value)
    data[0x100:0x110]=bytes(range(1,17))
    data[0x110:0x118]=bytes(range(0xa0,0xa8))
    return bytes(data)

if __name__=='__main__':
    if len(sys.argv)!=2:
        raise SystemExit('Usage: make_fixture_v12.py path/to/synthetic.dol')
    Path(sys.argv[1]).write_bytes(fixture())
