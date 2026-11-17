#!/usr/bin/env python3
"""V31 original continuous __start through Wii low-memory boot-info handoff.

Reuses verified V30 original SHA-pinned private image. The 30 authentic
PowerPC instructions are extracted only from the user-owned DOL at runtime.
No game code, assets or generated translation is bundled here.
"""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import struct
from make_start_to_hid4_v30 import make as make_v30, OSINIT, STOP as PREV_STOP
from make_hardware_boundary_v17 import ORIGINAL_SHA, get_text
from make_osinit_lowmem_v31 import validate as validate_lowmem
from make_start_to_data_v23 import SC,BLR

STOP=0x80520778


def make(owner:Path)->bytes:
    original=owner.read_bytes()
    if hashlib.sha256(original).hexdigest()!=ORIGINAL_SHA:
        raise ValueError("owner original Wii DOL SHA-256 mismatch")
    result=bytearray(make_v30(owner))
    off,guest,n=(struct.unpack_from(">I",result,k+4)[0]
                  for k in (0,0x48,0x90))
    if (off<256 or guest!=OSINIT or n < STOP+8-OSINIT
            or off+n>len(result)):
        raise ValueError("V30 inherited original OSInit section geometry changed")
    at=off+PREV_STOP-guest
    if result[at:at+8]!=struct.pack(">II",SC,BLR):
        raise ValueError("V30 exact original-PC stop is missing")
    continuation=get_text(original,PREV_STOP,STOP-PREV_STOP)
    validate_lowmem(continuation)
    result[at:at+len(continuation)]=continuation
    result[off+STOP-guest:off+STOP-guest+8]=struct.pack(">II",SC,BLR)
    return bytes(result)


def main()->None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("owner_dol",type=Path)
    parser.add_argument("private_output_dol",type=Path)
    args=parser.parse_args()
    if args.private_output_dol.exists() or args.private_output_dol.is_symlink():
        parser.error("refusing overwrite of original-owner image")
    args.private_output_dol.write_bytes(make(args.owner_dol))
    print("PASS: V31 authentic 30-instruction low-memory OSInit continuation prepared privately")

if __name__=="__main__":
    main()
