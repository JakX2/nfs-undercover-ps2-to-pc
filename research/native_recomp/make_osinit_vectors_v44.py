#!/usr/bin/env python3
"""Prepare owner-private V44 Wii exception vector-loop test DOL.

Original instruction bytes come only from the SHA-256 verified owner's Wii DOL.
The V43 builder provides all prior original functions and fail-closed guards.
No original-game instruction bytes are distributed by this source file.
"""
import argparse
import struct
from pathlib import Path
from make_osinit_cache_v43 import make as make_v43, END_STOP as OLD_STOP
from make_osinit_execparams_v28 import text_at, target, SC, BLR
from make_osinit_hid4_v30 import be32, OSINIT

NEXT_STOP = 0x80520E58  # original terminal DBPrintf call: synthetic stop
EXCEPTION = 0x80520BF4
DBPRINTF = 0x804E50B8
VECTOR_LOOP = 0x80520CA8


def make(owner: Path) -> bytes:
    image = bytearray(make_v43(owner))  # ancestor enforces owner DOL SHA
    original = owner.read_bytes()
    code = text_at(original, OLD_STOP, NEXT_STOP - OLD_STOP)
    if len(code) != 0xA0:
        raise ValueError('original exception-loop continuation has unexpected length')
    if be32(code, 0) != 0x3BBD0001 or be32(code, 4) != 0x281D000F:
        raise ValueError('original PPC exception iteration increment/bound changed')
    if be32(code, 8) != 0x4180FEE8:
        raise ValueError('original PPC exception loopback branch changed')
    if be32(code, 0x98) != 0x937C0000:
        raise ValueError('original exception-template restoration changed')
    if be32(code, 0x9C) != 0x4CC63182:
        raise ValueError('original CR field cleanup changed')
    finish = text_at(original, NEXT_STOP, 4)
    if target(be32(finish, 0), NEXT_STOP, True) != DBPRINTF:
        raise ValueError('end-of-exception debug service call target changed')
    off, guest, length = (be32(image, pos) for pos in (0, 0x48, 0x90))
    if guest != OSINIT or off < 0x100 or NEXT_STOP + 8 > guest + length:
        raise ValueError('unexpected inherited guest text section bounds')
    if be32(image, off + OLD_STOP - guest) != SC or be32(image, off + OLD_STOP + 4 - guest) != BLR:
        raise ValueError('inherited V43 exception stop mutated')
    for pc in range(OLD_STOP + 8, NEXT_STOP + 8, 4):
        if be32(image, off + pc - guest) != 0x60000000:
            raise ValueError('original exception-loop continuation overlaps previous test fixture')
    image[off + OLD_STOP-guest:off + NEXT_STOP-guest] = code
    struct.pack_into('>II', image, off + NEXT_STOP - guest, SC, BLR)
    return bytes(image)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('original_owner_dol', type=Path)
    ap.add_argument('private_destination', type=Path)
    args = ap.parse_args()
    if args.private_destination.exists():
        ap.error('refusing to overwrite an existing private DOL')
    args.private_destination.write_bytes(make(args.original_owner_dol))
    print('PASS: original Wii exception-loop test DOL created privately')
