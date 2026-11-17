#!/usr/bin/env python3
"""Verify private original 0x80520700..0x80520778 continuous Wii OSInit slice."""
import argparse
import hashlib
from pathlib import Path
import struct

from make_start_to_lowmem_v31 import make,STOP,PREV_STOP,OSINIT
from make_hardware_boundary_v17 import ORIGINAL_SHA,get_text
from make_osinit_lowmem_v31 import validate as validate_original
from make_start_to_data_v23 import SC,BLR


def verify(image:bytes,source:bytes)->None:
    if hashlib.sha256(source).hexdigest()!=ORIGINAL_SHA:
        raise ValueError("wrong owner DOL hash")
    if len(image)<256 or struct.unpack_from(">I",image,0xe0)[0]!=0x8000403C:
        raise ValueError("not the authentic continuous Wii startup entry")
    off,guest,n=(struct.unpack_from(">I",image,k+4)[0]
                 for k in (0,0x48,0x90))
    if off<256 or guest!=OSINIT or n<STOP+8-OSINIT or off+n>len(image):
        raise ValueError("private Wii DOL OSInit out of bounds")
    code=image[off+PREV_STOP-guest:off+STOP-guest]
    validate_original(code)
    if code!=get_text(source,PREV_STOP,STOP-PREV_STOP):
        raise ValueError("original low-memory instruction span mismatch")
    if image[off+STOP-guest:off+STOP-guest+8]!=struct.pack(">II",SC,BLR):
        raise ValueError("expected exact test-only V31 stop at 0x80520778")
    guest_regions=[]
    for i in range(7):
        off,addr,count=(struct.unpack_from(">I",image,k+4*i)[0]
                        for k in (0,0x48,0x90))
        if count<4 or off<256 or off+count>len(image):
            raise ValueError("malformed original PPC segment geometry")
        for left,right in guest_regions:
            if not(addr>=right or addr+count<=left):
                raise ValueError("overlapping PowerPC guest code")
        guest_regions.append((addr,addr+count))


def main()->None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("private_dol",type=Path)
    parser.add_argument("original_dol",type=Path)
    args=parser.parse_args()
    verify(args.private_dol.read_bytes(),args.original_dol.read_bytes())
    print("PASS: V31 authentic low-memory boot-info guest instructions and exact stop verified privately")

if __name__=="__main__":
    main()
