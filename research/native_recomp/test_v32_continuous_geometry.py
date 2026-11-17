#!/usr/bin/env python3
"""Private SHA-verified V32 MEM1 setter geometry regression."""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import struct

from make_start_to_arena_v32 import OSINIT,LO,HI,STOP,be32
from make_osinit_arena_v32 import validate_os,validate_setter
from make_hardware_boundary_v17 import ORIGINAL_SHA,get_text
from make_start_to_data_v23 import SC,BLR


def mapped(image:bytes,index:int,pc:int,count:int)->bytes:
    off,guest,size=(be32(image,field+4*index) for field in (0,0x48,0x90))
    if off<256 or guest>pc or pc+count>guest+size or off+size>len(image):
        raise ValueError("private owner Wii DOL section out of bounds")
    return image[off+pc-guest:off+pc-guest+count]


def verify(image:bytes,original:bytes)->None:
    if hashlib.sha256(original).hexdigest()!=ORIGINAL_SHA:
        raise ValueError("original Wii game DOL SHA mismatch")
    if len(image)<256 or be32(image,0xe0)!=0x8000403C:
        raise ValueError("wrong original __start executable entry")
    code=mapped(image,1,0x80520778,STOP-0x80520778)
    validate_os(code)
    if code != get_text(original,0x80520778,STOP-0x80520778):
        raise ValueError("original Wii MEM1 decision code differs")
    if mapped(image,1,STOP,8)!=struct.pack(">II",SC,BLR):
        raise ValueError("V32 exact 0x80520818 syscall stop is missing")
    for setter in (LO,HI):
        body=mapped(image,1,setter,8)
        validate_setter(body,setter)
        if body!=get_text(original,setter,8):
            raise ValueError("original Wii MEM1 setter body differs")
    segments=[]
    for i in range(7):
        off,guest,size=(be32(image,field+4*i) for field in (0,0x48,0x90))
        if off<256 or size<4 or off+size>len(image):
            raise ValueError("invalid private bounded Wii DOL geometry")
        for a,b in segments:
            if not (guest>=b or guest+size<=a):
                raise ValueError("overlapping original Wii code mappings")
        segments.append((guest,guest+size))


def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_dol",type=Path)
    p.add_argument("original_owner_dol",type=Path)
    a=p.parse_args()
    verify(a.private_dol.read_bytes(),a.original_owner_dol.read_bytes())
    print("PASS: exact original Wii MEM1 arena native setter geometry and test stop")


if __name__=="__main__":
    main()
