#!/usr/bin/env python3
"""V36 continuous Wii __start: original exception-mark helper and branch.

Construct only a private SHA-pinned owner Wii PPC test DOL. The authentic
instruction bytes never enter this repository or CI artifact uploads.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import hashlib
import struct

from make_start_to_exception_v35 import (
    make as make_v35, OSINIT, STOP as PREVIOUS_STOP, word
)
from make_osinit_dbmark_v40 import (
    MARK, MARK_LENGTH, FIRST_STOP, SECOND_STOP
)
from make_start_to_dbinit_v24 import DBINIT
from make_hardware_boundary_v17 import ORIGINAL_SHA, get_text, linked_target
from make_start_to_data_v23 import SC, BLR, NOP

STOP = SECOND_STOP
MARK_FIRST = FIRST_STOP


def make(owner: Path) -> bytes:
    original = owner.read_bytes()
    if hashlib.sha256(original).hexdigest() != ORIGINAL_SHA:
        raise ValueError("original Wii owner DOL SHA mismatch")
    prev = make_v35(owner)
    sections = []
    for i in range(7):
        off, guest, size = (word(prev, field + i * 4)
                            for field in (0, 0x48, 0x90))
        if off < 256 or size < 4 or off + size > len(prev):
            raise ValueError("malformed inherited V35 original guest section")
        sections.append((guest, bytearray(prev[off:off + size])))
    if sections[1][0] != OSINIT or sections[6][0] != DBINIT:
        raise ValueError("V35 OSInit / DBInit guest sections changed")

    body = get_text(original, PREVIOUS_STOP, STOP - PREVIOUS_STOP)
    helper = get_text(original, MARK, MARK_LENGTH)
    if len(body) != 0x4C or len(helper) != 24 or word(helper,20) != BLR:
        raise ValueError("truncated original exception-mark branch/helper")
    if word(body,0) != 0x806DF244:
        raise ValueError("original Wii exception control-flow state changed")
    for site in (0x80520CC4, 0x80520CF0):
        if linked_target(word(body, site-PREVIOUS_STOP), site) != MARK:
            raise ValueError("original exception-marker BL target changed")

    guest, os = sections[1]
    at = PREVIOUS_STOP - guest
    if os[at:at+8] != struct.pack(">II",SC,BLR):
        raise ValueError("V35 bounded exception stop missing")
    if STOP + 8 > guest + len(os):
        raise ValueError("new exception-mark guard exceeds prior OSInit section")
    # Restore only the owner-original 0x4c-byte exception continuation, plus
    # exact test-only stops at the two original marker-return PCs.
    os[at:STOP-guest] = body
    struct.pack_into(">II",os,MARK_FIRST-guest,SC,BLR)
    struct.pack_into(">II",os,STOP-guest,SC,BLR)
    sections[1] = (guest,os)

    guest, debug = sections[6]
    mark_at = MARK - guest
    if mark_at < 40 or mark_at + MARK_LENGTH > len(debug):
        raise ValueError("original mark helper outside existing DBInit gap")
    if debug[mark_at:mark_at+MARK_LENGTH] != NOP.to_bytes(4,"big")*6:
        raise ValueError("original debug marker overlaps existing native function")
    debug[mark_at:mark_at+MARK_LENGTH] = helper
    sections[6] = (guest,debug)

    data_off,data_size = word(prev,0x1c),word(prev,0xac)
    if data_off<256 or data_size!=0xB0 or data_off+data_size>len(prev):
        raise ValueError("owner-original startup data section corrupted")
    data = prev[data_off:data_off+data_size]
    image = bytearray(256+sum((len(blob)+3)&~3 for _,blob in sections)+len(data))
    cursor = 256
    for i,(guest,blob) in enumerate(sections):
        for field,value in ((0,cursor),(0x48,guest),(0x90,len(blob))):
            struct.pack_into(">I",image,field+4*i,value)
        image[cursor:cursor+len(blob)] = blob
        cursor += (len(blob)+3)&~3
    for field,value in ((0x1c,cursor),(0x64,0x80006420),(0xac,len(data))):
        struct.pack_into(">I",image,field,value)
    image[cursor:cursor+len(data)] = data
    struct.pack_into(">I",image,0xE0,0x8000403C)
    return bytes(image)


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("owner_dol",type=Path)
    parser.add_argument("private_output_dol",type=Path)
    args=parser.parse_args()
    if args.private_output_dol.exists() or args.private_output_dol.is_symlink():
        parser.error("refusing overwrite of existing private owner test DOL")
    args.private_output_dol.write_bytes(make(args.owner_dol))
    print("PASS: V36 owner-original continuous exception-marker fixture generated privately")
