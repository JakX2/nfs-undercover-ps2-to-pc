#!/usr/bin/env python3
"""Fail-closed owner-private original MEM2 code/arena DOL geometry checks."""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import struct

from make_start_to_mem2_v33 import OSINIT,STOP,MEM2_LO,MEM2_HI,word
from make_osinit_mem2_v37 import OLD_STOP,check_source,check_setter
from make_osinit_arena_v32 import validate_os as validate_mem1
from make_hardware_boundary_v17 import ORIGINAL_SHA,get_text
from make_start_to_data_v23 import SC,BLR


def mapped(image:bytes,index:int,pc:int,count:int)->bytes:
    off,base,size=(word(image,field+4*index) for field in (0,0x48,0x90))
    if off<256 or count<=0 or pc<base or pc+count>base+size or off+size>len(image):
        raise ValueError("original Wii native test code outside mapped private DOL")
    return image[off+pc-base:off+pc-base+count]


def verify(image:bytes,original:bytes)->None:
    if hashlib.sha256(original).hexdigest()!=ORIGINAL_SHA:
        raise ValueError("wrong original Wii DOL SHA-256")
    if len(image)<256 or word(image,0xe0)!=0x8000403C:
        raise ValueError("wrong continuous original Wii entry")
    if word(image,0x48+4)!=OSINIT:
        raise ValueError("original OSInit guest section changed")
    mem1=mapped(image,1,0x80520778,OLD_STOP-0x80520778)
    validate_mem1(mem1)
    if mem1!=get_text(original,0x80520778,len(mem1)):
        raise ValueError("original MEM1 code was changed")
    mem2=mapped(image,1,OLD_STOP,STOP-OLD_STOP)
    check_source(mem2)
    if mem2!=get_text(original,OLD_STOP,STOP-OLD_STOP):
        raise ValueError("original MEM2 selector code was changed")
    if mapped(image,1,STOP,8)!=struct.pack(">II",SC,BLR):
        raise ValueError("missing exact 0x805208A4 synthetic terminal syscall")
    for pc in (MEM2_LO,MEM2_HI):
        body=mapped(image,1,pc,8)
        check_setter(body,pc)
        if body!=get_text(original,pc,8):
            raise ValueError("original MEM2 setter code differs from owner")
    # Data table is an original relocator input, not an extra fake code section.
    data_off,data_base,data_size=(word(image,k) for k in (0x1c,0x64,0xac))
    if data_off<256 or data_base!=0x80006420 or data_size!=0xB0 or data_off+data_size>len(image):
        raise ValueError("original relocation data section changed")
    regions=[]
    for i in range(7):
        off,guest,count=(word(image,k+4*i) for k in (0,0x48,0x90))
        if off<256 or count<4 or off+count>len(image) or guest&3:
            raise ValueError("unsafe private Wii DOL code bounds")
        for a,b in regions:
            if not (guest>=b or guest+count<=a):
                raise ValueError("overlapping PowerPC guest code regions")
        regions.append((guest,guest+count))


def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_dol",type=Path)
    p.add_argument("original_owner_dol",type=Path)
    a=p.parse_args()
    verify(a.private_dol.read_bytes(),a.original_owner_dol.read_bytes())
    print("PASS: V33 original continuous MEM2 arena body and strict DOL geometry")


if __name__=="__main__":
    main()
