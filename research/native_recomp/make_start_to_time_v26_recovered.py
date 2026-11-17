#!/usr/bin/env python3
"""Recover the private continuous V26 Wii startup slice using the V25 fixture.

Only independently written source is stored here. Extract authentic
PowerPC instructions at runtime from the exact SHA-256-pinned owner DOL.
Synthetic mode deliberately retains the existing V25 independent fixture.
This is a controlled native test boundary, not full hardware or a game boot.
"""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import struct

from make_osinit_prefix_v25 import make as make_v25
from make_start_to_dbinit_v24 import OSINIT, be32
from make_hardware_boundary_v17 import ORIGINAL_SHA, get_text, linked_target
from make_start_to_data_v23 import SC, BLR, NOP

TIME = 0x8052A844
GETTIME = 0x8052A824
DISABLE = 0x805265AC
RESTORE = 0x805265D4
CACHE = 0x80522540
SAVE20 = 0x805450E8
STOP = 0x805206B4
START = 0x8000403C


def make(owner: Path | None) -> bytes:
    old = make_v25(owner)
    if owner is None:
        # Keep the independently authored V25 synthetic stimulus unchanged.
        return old
    original = owner.read_bytes()
    if hashlib.sha256(original).hexdigest() != ORIGINAL_SHA:
        raise ValueError("owner original image SHA-256 mismatch")
    sections: list[tuple[int, bytearray]] = []
    for i in range(7):
        offset, address, length = (be32(old, base + 4 * i)
                                    for base in (0, 0x48, 0x90))
        if offset < 256 or length < 4 or offset + length > len(old):
            raise ValueError("V25 parent section geometry invalid")
        sections.append((address, bytearray(old[offset:offset+length])))
    if sections[1][0] != OSINIT or sections[5][0] != CACHE:
        raise ValueError("unexpected bounded original section addresses")
    address, os_text = sections[1]
    if be32(os_text, 0x3c) != BLR:
        raise ValueError("V25 OS-time synthetic stop changed")
    # Original OSInit's timestamp high and low stores follow its original
    # time service call. The next BL is temporarily intercepted by test SC.
    tail = get_text(original, OSINIT + 0x3c, 12)
    if linked_target(be32(tail, 8), STOP) != DISABLE:
        raise ValueError("original post-time interrupt-disable call changed")
    os_text[0x3c:0x44] = tail[:8]
    os_text[0x44:0x4c] = struct.pack(">II", SC, BLR)
    sections[1] = (address, os_text)

    address, cache_text = sections[5]
    end = RESTORE + 36
    new_size = end - CACHE
    if not len(cache_text) < new_size < 200_000 or new_size & 3:
        raise ValueError("invalid time/interrupt helper memory geometry")
    cache_text += NOP.to_bytes(4, "big") * ((new_size - len(cache_text)) // 4)
    # Keep the existing genuine CACHE and SAVE20 functions from V25; insert
    # all four verified original helpers as separate non-overlapping spans.
    spans = ((GETTIME, 24), (TIME, 100), (DISABLE, 20), (RESTORE, 36))
    for guest, length in spans:
        start = guest - CACHE
        if start < 0 or start + length > len(cache_text):
            raise ValueError("helper lies outside private bounded DOL section")
        cache_text[start:start+length] = get_text(original, guest, length)
    sections[5] = (address, cache_text)

    data_off, data_size = be32(old, 0x1c), be32(old, 0xac)
    if data_size != 0xb0 or data_off < 256 or data_off + data_size > len(old):
        raise ValueError("V25 BSS/data table missing")
    table = old[data_off:data_off+data_size]
    image = bytearray(256 + sum((len(part) + 3) & ~3 for _, part in sections) + len(table))
    pos = 256
    for i, (guest, payload) in enumerate(sections):
        for field, val in ((0, pos), (0x48, guest), (0x90, len(payload))):
            struct.pack_into(">I", image, field+4*i, val)
        image[pos:pos+len(payload)] = payload
        pos += (len(payload)+3) & ~3
    for field, val in ((0x1c, pos), (0x64, 0x80006420), (0xac, len(table))):
        struct.pack_into(">I", image, field, val)
    image[pos:pos+len(table)] = table
    struct.pack_into(">I", image, 0xe0, START)
    return bytes(image)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--owner-dol", type=Path)
    args = parser.parse_args()
    if args.output.exists() or args.output.is_symlink():
        parser.error("refusing to overwrite a private image")
    image = make(args.owner_dol)
    args.output.write_bytes(image)
    print("PASS: V26 recovered bounded startup fixture created privately")


if __name__ == "__main__":
    main()
