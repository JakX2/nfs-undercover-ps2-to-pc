#!/usr/bin/env python3
"""Generate two independent original-free PowerPC functions with one BL edge.

At 0x80004000: mflr r0; stw r0,8(r1); bl leaf; lwz r0,8(r1);
               mtlr r0; blr
At 0x80004018: addi r3,r3,1; blr
"""
import struct
import sys
from pathlib import Path


def fixture():
    b = bytearray(0x120)
    for offset, value in (
        (0x00, 0x100), (0x48, 0x80004000), (0x90, 32),
        (0xE0, 0x80004000),
    ):
        struct.pack_into('>I', b, offset, value)
    opcodes = (
        0x7C0802A6,  # mflr r0
        0x90010008,  # stw r0,8(r1)
        0x48000011,  # bl +0x10
        0x80010008,  # lwz r0,8(r1)
        0x7C0803A6,  # mtlr r0
        0x4E800020,  # blr
        0x38630001,  # addi r3,r3,1
        0x4E800020,  # blr
    )
    for i, opcode in enumerate(opcodes):
        struct.pack_into('>I', b, 0x100 + 4*i, opcode)
    return bytes(b)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Usage: make_synthetic_callgraph_v14.py OUTPUT.DOL')
    Path(sys.argv[1]).write_bytes(fixture())
