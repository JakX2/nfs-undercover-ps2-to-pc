#!/usr/bin/env python3
"""Create a tiny independent PPC leaf fixture, not using Undercover bytes.

Two simple hand-authored synthetic PPC functions are adjacent in text:
  add1:  addi r3,r3,1 ; blr
  store: lbz r5,0(r4) ; stb r5,0(r3) ; blr
"""
import struct
import sys
from pathlib import Path


def fixture():
    image = bytearray(0x114)
    def be32(where, value):
        struct.pack_into('>I', image, where, value)
    be32(0x00, 0x100)       # text[0] file offset
    be32(0x48, 0x80004000)  # text[0] guest address
    be32(0x90, 20)          # text[0] size
    be32(0xE0, 0x80004000)  # entry point
    for i, opcode in enumerate((0x38630001, 0x4E800020,
                                0x88A40000, 0x98A30000, 0x4E800020)):
        be32(0x100 + i * 4, opcode)
    return bytes(image)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Usage: make_synthetic_dol_v13.py OUTPUT.DOL')
    Path(sys.argv[1]).write_bytes(fixture())
