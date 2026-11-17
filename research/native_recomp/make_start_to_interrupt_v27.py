#!/usr/bin/env python3
"""Private recovered V27 continuous Wii __start interrupt-disable seam.

Starts from the SHA-pinned, already verified V26 continuous native fixture.
Original new PowerPC instructions are copied only from owner DOL at runtime.
End with test-only SC before entering original __OSGetExecParams.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import hashlib
import struct

from make_start_to_time_v26_recovered import make as make_v26
from make_hardware_boundary_v17 import ORIGINAL_SHA, get_text, linked_target
from make_start_to_data_v23 import SC, BLR

PREVIOUS_STOP = 0x805206B4
NEXT_STOP = 0x805206BC
DISABLE = 0x805265AC
EXEC_PARAMS = 0x80523B1C


def make(owner: Path) -> bytes:
    original = owner.read_bytes()
    if hashlib.sha256(original).hexdigest() != ORIGINAL_SHA:
        raise ValueError("owner original Wii image SHA-256 mismatch")
    result = bytearray(make_v26(owner))
    # Reuse the proven V26 original DOL section geometry unchanged.
    section = 1
    off, guest, length = (struct.unpack_from(">I", result, base + 4*section)[0]
                          for base in (0, 0x48, 0x90))
    if (off < 256 or guest > PREVIOUS_STOP or
            NEXT_STOP + 8 > guest + length or
            off + length > len(result)):
        raise ValueError("invalid recovered OSInit segment geometry")
    loc = off + PREVIOUS_STOP - guest
    if result[loc:loc+8] != struct.pack(">II", SC, BLR):
        raise ValueError("previous V26 exact checkpoint guard missing")
    words = get_text(original, PREVIOUS_STOP, 12)
    if (linked_target(struct.unpack_from(">I", words, 0)[0], PREVIOUS_STOP) != DISABLE
            or linked_target(struct.unpack_from(">I", words, 8)[0], NEXT_STOP) != EXEC_PARAMS):
        raise ValueError("original OSInit interrupt/execparams calls changed")
    # Actually execute original BL at B4 and original fallthrough at B8.
    # Do not execute __OSGetExecParams yet; its BL is the NEXT genuine seam.
    result[loc:loc+8] = words[:8]
    result[loc+8:loc+16] = struct.pack(">II", SC, BLR)
    return bytes(result)


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("owner_dol",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    if a.output.exists() or a.output.is_symlink():
        p.error("refusing overwrite of owner-derived private test image")
    a.output.write_bytes(make(a.owner_dol))
    print("PASS: original V27 continuous interrupt-disable private fixture generated")


if __name__=="__main__":
    main()
