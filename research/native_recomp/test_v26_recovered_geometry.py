#!/usr/bin/env python3
"""Independent checks for recovered V26 private DOL test-image geometry."""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import struct
from make_start_to_time_v26_recovered import (
    make, CACHE, GETTIME, TIME, DISABLE, RESTORE, STOP, OSINIT, START
)
from make_osinit_prefix_v25 import make as v25
from make_hardware_boundary_v17 import ORIGINAL_SHA, get_text
from make_start_to_data_v23 import SC, BLR

def word(data: bytes, at: int) -> int:
    return struct.unpack_from(">I", data, at)[0]

def mapped(image: bytes, guest: int, length: int) -> bytes:
    for i in range(7):
        off, addr, size=(word(image,field+4*i) for field in (0,0x48,0x90))
        if off>=256 and size and addr<=guest and guest+length<=addr+size:
            return image[off+guest-addr:off+guest-addr+length]
    raise ValueError("missing bounded PowerPC guest mapping")

def validate(image: bytes, original: bytes | None) -> None:
    if len(image)<256 or word(image,0xe0)!=START:
        raise ValueError("recovered fixture has wrong original entry")
    if original is None:
        if image!=v25(None):
            raise ValueError("synthetic V25 data unexpectedly changed")
        return
    if hashlib.sha256(original).hexdigest()!=ORIGINAL_SHA:
        raise ValueError("owner original DOL SHA mismatch")
    if mapped(image,STOP,8)!=struct.pack(">II",SC,BLR):
        raise ValueError("recovered original V26 exact syscall boundary changed")
    for at,span in ((OSINIT,0x44),(GETTIME,24),(TIME,100),
                    (DISABLE,20),(RESTORE,36)):
        if mapped(image,at,span)!=get_text(original,at,span):
            raise ValueError("private original Wii instruction span mismatch")
    # The original __start entry and distinct time, cache and helper addresses
    # must all be mapped without overlapping DOL sections.
    for at in (START,OSINIT,CACHE,GETTIME,TIME,DISABLE,RESTORE):
        mapped(image,at,4)
    file_regions,guest_regions=[],[]
    for i in range(7):
        off,addr,size=(word(image,field+4*i) for field in (0,0x48,0x90))
        if not(size and off>=256 and off+size<=len(image) and
               addr>=0x80000000 and addr+size<=0x81800000):
            raise ValueError("invalid recovered private DOL geometry")
        for begin,end in file_regions:
            if not(off>=end or off+size<=begin):
                raise ValueError("overlapping private DOL file sections")
        for begin,end in guest_regions:
            if not(addr>=end or addr+size<=begin):
                raise ValueError("overlapping private Wii guest regions")
        file_regions.append((off,off+size));guest_regions.append((addr,addr+size))

def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("image",type=Path)
    p.add_argument("--owner-dol",type=Path)
    a=p.parse_args()
    original=a.owner_dol.read_bytes() if a.owner_dol else None
    validate(a.image.read_bytes(),original)
    print("PASS: recovered V26 fixture exact private PowerPC span and stop geometry")

if __name__=="__main__":
    main()
