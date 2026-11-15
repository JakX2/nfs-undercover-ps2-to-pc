#!/usr/bin/env python3
"""Private V41 exception-setup slice: original marked paths and template clear loop.

Owner's SHA-pinned Wii executable supplies every genuine instruction. The
original PowerPC text and generated translated C++ remain in a private fixture.
Only explicit debugger-service and pre-vector-copy stops are synthesized.
"""
import argparse
import struct
from pathlib import Path

from make_osinit_dbmark_v40 import make as make_v40, OSINIT
from make_osinit_execparams_v28 import text_at, SC, BLR
from make_osinit_hid4_v30 import be32

FIRST_DEBUG = 0x80520CDC  # original DBPrintf call, now a strict test guard
SECOND_DEBUG = 0x80520D08  # second original DBPrintf call, now strict guard
VECTOR_COPY_STOP = 0x80520D80  # stop BEFORE original vector-target computation
FIRST_ORIGINAL = 0x80520CC8
ORIGINAL_END = VECTOR_COPY_STOP


def make(owner: Path) -> bytes:
    private = bytearray(make_v40(owner))  # strict original SHA and earlier checks
    original = Path(owner).read_bytes()
    # Copy an uninterrupted owner-original branch/loop region from the first
    # marker's return through the last template-store loop instruction.
    original_body = text_at(original, FIRST_ORIGINAL, ORIGINAL_END - FIRST_ORIGINAL)
    if len(original_body) != 0xB8:
        raise ValueError('unexpected original exception-loop length')
    # Verify both branch sites before editing test boundaries.
    for pc, opcode in ((0x80520CC8, 0x2C030000),
                       (0x80520CCC, 0x41820018),
                       (0x80520CF4, 0x2C030000),
                       (0x80520CF8, 0x41820028),
                       (0x80520D20, 0x28150000),
                       (0x80520D64, 0x4200FFDC),
                       (0x80520D7C, 0x4200FFF8)):
        if be32(original_body, pc - FIRST_ORIGINAL) != opcode:
            raise ValueError('original exception-template branch or loop changed')
    for pc in (FIRST_DEBUG, SECOND_DEBUG):
        if be32(original_body, pc - FIRST_ORIGINAL) >> 26 != 18:
            raise ValueError('expected original debug call missing')
    # V40 merged OSInit/exception section starts at OSINIT.
    offset = be32(private, 0)
    address = be32(private, 0x48)
    length = be32(private, 0x90)
    if address != OSINIT or not offset >= 0x100 or not address <= FIRST_ORIGINAL:
        raise ValueError('unknown inherited original guest section')
    if ORIGINAL_END + 8 > address + length:
        raise ValueError('exception continuation extends beyond private image')
    private[offset + FIRST_ORIGINAL - address:
            offset + ORIGINAL_END - address] = original_body
    for pc in (FIRST_DEBUG, SECOND_DEBUG, VECTOR_COPY_STOP):
        location = offset + pc - address
        struct.pack_into('>I', private, location, SC)
        if pc == VECTOR_COPY_STOP:
            struct.pack_into('>I', private, location + 4, BLR)
    return bytes(private)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('owner_dol', type=Path)
    parser.add_argument('private_destination', type=Path)
    args = parser.parse_args()
    if args.private_destination.exists():
        parser.error('refusing to overwrite existing private slice')
    args.private_destination.write_bytes(make(args.owner_dol))
    print('PASS: V41 private original exception template-clear image constructed')
