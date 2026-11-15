#!/usr/bin/env python3
"""Create an owner-private OSExceptionInit vector memcpy test image.

All source PPC and template bytes come exclusively from a SHA-pinned owner DOL.
The test-only data section carries a private verification oracle. Nothing
proprietary is embedded in or printed from this standalone source file.
"""
import argparse
import struct
from pathlib import Path

from make_osinit_vectorclear_v41 import make as make_v41, OSINIT, FIRST_DEBUG, SECOND_DEBUG
from make_osinit_execparams_v28 import text_at, target, SC, BLR
from make_osinit_hid4_v30 import be32

COPY_START = 0x80520D80
COPY_CALL = 0x80520D98
CACHE_STOP = 0x80520DA4  # before original DCFlushRangeNoSync
CACHE_FUNC = 0x80522320
MEMCPY = 0x80004338
TEMPLATE_SRC = 0x80520EC0
TEMPLATE_SIZE = 0x98
PRIVATE_DATA_GUEST = 0x90050000  # fixture-only MEM2 address, never executable


def make(owner: Path) -> bytes:
    parent = bytearray(make_v41(owner))  # verifies original DOL SHA
    raw = owner.read_bytes()
    new_code = text_at(raw, COPY_START, CACHE_STOP - COPY_START)
    template = text_at(raw, TEMPLATE_SRC, TEMPLATE_SIZE)
    if len(new_code) != 36 or len(template) != TEMPLATE_SIZE:
        raise ValueError('original vector copy or handler template truncated')
    if target(be32(new_code, COPY_CALL-COPY_START), COPY_CALL, True) != MEMCPY:
        raise ValueError('original vector copy does not call expected memcpy')
    next_code = text_at(raw, CACHE_STOP, 4)
    if target(be32(next_code, 0), CACHE_STOP, True) != CACHE_FUNC:
        raise ValueError('original Wii cache flush callsite changed')
    first_off, first_guest, first_length = (be32(parent, p) for p in (0, 0x48, 0x90))
    if first_guest != OSINIT or not first_off >= 0x100 or COPY_START < OSINIT:
        raise ValueError('unexpected V41 private image text geometry')
    if CACHE_STOP+8 > first_guest+first_length:
        raise ValueError('vector continuation falls beyond original text section')
    if be32(parent, first_off + COPY_START-first_guest) != SC:
        raise ValueError('original V41 vector computation stop is missing')
    parent[first_off + COPY_START-first_guest:
           first_off + CACHE_STOP-first_guest] = new_code
    struct.pack_into('>II', parent, first_off+CACHE_STOP-first_guest, SC, BLR)
    # The parent uses all seven PPC text slots. Add one DOL data segment to
    # retain the owner's authentic handler template independently of the
    # executable analyzer guards at the original source address.
    if any(be32(parent, p) for p in (0x1c, 0x64, 0xac)):
        raise ValueError('unexpected inherited nonempty data section')
    data_off = (len(parent)+3)&~3
    parent.extend(b'\0'*(data_off-len(parent)))
    parent.extend(template)
    struct.pack_into('>I', parent, 0x1c, data_off)
    struct.pack_into('>I', parent, 0x64, PRIVATE_DATA_GUEST)
    struct.pack_into('>I', parent, 0xac, TEMPLATE_SIZE)
    return bytes(parent)


if __name__ == '__main__':
    p=argparse.ArgumentParser()
    p.add_argument('owner_dol', type=Path)
    p.add_argument('private_destination', type=Path)
    a=p.parse_args()
    if a.private_destination.exists():p.error('refusing to overwrite existing private test image')
    a.private_destination.write_bytes(make(a.owner_dol))
    print('PASS: V42 SHA-pinned private Wii exception-vector copy image built')
