#!/usr/bin/env python3
"""Verify private original V28 continuous-execparams fixture without logging code."""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import struct

from make_start_to_execparams_v28 import EXEC_CALL, EXEC, STOP, section_offset
from make_hardware_boundary_v17 import ORIGINAL_SHA, get_text, linked_target
from make_start_to_data_v23 import SC, BLR

def verify(image: bytes, original: bytes) -> None:
    if hashlib.sha256(original).hexdigest() != ORIGINAL_SHA:
        raise ValueError("original owner DOL SHA-256 mismatch")
    if len(image) < 256 or struct.unpack_from(">I",image,0xe0)[0] != 0x8000403C:
        raise ValueError("continuous original startup entry changed")
    at = section_offset(image,1,EXEC_CALL,12)
    call = struct.unpack_from(">I",image,at)[0]
    if linked_target(call,EXEC_CALL) != EXEC:
        raise ValueError("original execparams direct call target changed")
    if image[at+4:at+12] != struct.pack(">II",SC,BLR):
        raise ValueError("V28 control stop must precede later OSInit services")
    if image[section_offset(image,5,EXEC,36):][:36] != get_text(original,EXEC,36):
        raise ValueError("authentic original execparams body is not complete")
    # Exact function geometry in the inherited seven-section bounded DOL.
    file_regions, guest_regions = [], []
    for i in range(7):
        off, addr, size = (struct.unpack_from(">I",image,field+4*i)[0]
                            for field in (0,0x48,0x90))
        if off < 256 or size < 4 or off+size > len(image):
            raise ValueError("invalid original Wii text section bounds")
        for first,last in file_regions:
            if not (off >= last or off+size <= first):
                raise ValueError("overlapping private text-file ranges")
        for first,last in guest_regions:
            if not (addr >= last or addr+size <= first):
                raise ValueError("overlapping guest text ranges")
        file_regions.append((off,off+size))
        guest_regions.append((addr,addr+size))

def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_dol",type=Path)
    p.add_argument("owner_original",type=Path)
    args=p.parse_args()
    verify(args.private_dol.read_bytes(),args.owner_original.read_bytes())
    print("PASS: original Wii V28 execparams call, body and controlled PC geometry")

if __name__=="__main__":
    main()
