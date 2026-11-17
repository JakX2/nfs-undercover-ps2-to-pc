#!/usr/bin/env python3
"""Owner-private V33 continuous Wii __start -> genuine MEM2 arena selection.

Copies only SHA-pinned original PowerPC bytes into private runner scratch.
Uses the separately verified original direct-entry V37 source signatures;
never publishes game instruction bytes or generated C++.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import struct

from make_start_to_arena_v32 import make as make_v32
from make_osinit_mem2_v37 import (
    STOP, OLD_STOP, MEM2_LO, MEM2_HI,
    check_source, check_setter,
)
from make_hardware_boundary_v17 import ORIGINAL_SHA, get_text
from make_start_to_data_v23 import SC, BLR, NOP

OSINIT = 0x80520670
NEXT_SECTION = 0x80522280


def word(image: bytes, at: int) -> int:
    return struct.unpack_from(">I", image, at)[0]


def make(owner: Path) -> bytes:
    raw = owner.read_bytes()
    if hashlib.sha256(raw).hexdigest() != ORIGINAL_SHA:
        raise ValueError("owner-original Wii DOL does not match SHA-256")
    prior = make_v32(owner)
    sections = []
    for i in range(7):
        off, guest, size = (word(prior, base + i * 4)
                            for base in (0, 0x48, 0x90))
        if off < 256 or size <= 0 or off + size > len(prior):
            raise ValueError("malformed inherited V32 private DOL text sections")
        sections.append((guest, bytearray(prior[off:off+size])))
    if sections[1][0] != OSINIT or sections[3][0] != NEXT_SECTION:
        raise ValueError("V32 original startup function mapping changed")

    continuation = get_text(raw, OLD_STOP, STOP-OLD_STOP)
    check_source(continuation)
    os = sections[1][1]
    if os[OLD_STOP-OSINIT:OLD_STOP-OSINIT+8] != struct.pack(">II", SC, BLR):
        raise ValueError("V32 synthetic MEM1->MEM2 stop is missing")

    # Extend the existing OSInit/PPC hardware region eight bytes to fit MEM2Lo.
    # No guest code region may overlap the following original DCEnable text.
    end = MEM2_LO + 8 - OSINIT
    if end <= len(os) or end > NEXT_SECTION-OSINIT or end & 3:
        raise ValueError("invalid contiguous Wii MEM2 helper section extension")
    os.extend(NOP.to_bytes(4, "big") * ((end-len(os))//4))
    os[OLD_STOP-OSINIT:STOP-OSINIT] = continuation
    os[STOP-OSINIT:STOP-OSINIT+8] = struct.pack(">II", SC, BLR)

    for guest in (MEM2_HI, MEM2_LO):
        body = get_text(raw, guest, 8)
        check_setter(body, guest)
        at = guest-OSINIT
        if os[at:at+8] != NOP.to_bytes(4, "big")*2:
            raise ValueError("MEM2 original setter overlaps an existing function")
        os[at:at+8] = body
    sections[1] = (OSINIT, os)

    data_off, data_size = word(prior, 0x1c), word(prior, 0xac)
    if data_off < 256 or data_size != 0xB0 or data_off+data_size > len(prior):
        raise ValueError("authentic Wii startup table not preserved")
    data = prior[data_off:data_off+data_size]
    output = bytearray(256+sum((len(part)+3)&~3 for _,part in sections)+len(data))
    at = 256
    for i, (guest, part) in enumerate(sections):
        for base, value in ((0, at), (0x48, guest), (0x90, len(part))):
            struct.pack_into(">I", output, base+i*4, value)
        output[at:at+len(part)] = part
        at += (len(part)+3)&~3
    for base,value in ((0x1c,at),(0x64,0x80006420),(0xac,len(data))):
        struct.pack_into(">I", output, base, value)
    output[at:at+len(data)] = data
    struct.pack_into(">I", output, 0xe0, 0x8000403C)
    return bytes(output)


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("owner_dol", type=Path)
    parser.add_argument("private_output_dol", type=Path)
    args=parser.parse_args()
    if args.private_output_dol.exists() or args.private_output_dol.is_symlink():
        parser.error("refusing existing private owner fixture overwrite")
    args.private_output_dol.write_bytes(make(args.owner_dol))
    print("PASS: original Wii continuous V33 MEM2 arena image generated in private scratch")


if __name__ == "__main__":
    main()
