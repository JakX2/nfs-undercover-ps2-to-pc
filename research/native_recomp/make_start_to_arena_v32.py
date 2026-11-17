#!/usr/bin/env python3
"""SHA-pinned original Wii __start -> OSInit -> MEM1 arena setters.

Only independently authored fixture construction is stored here.
Original PPC words are extracted exclusively from the private owner DOL.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import hashlib
import struct

from make_start_to_lowmem_v31 import make as make_v31, STOP as PREV_STOP
from make_hardware_boundary_v17 import ORIGINAL_SHA, get_text
from make_osinit_arena_v32 import (
    validate_os, validate_setter, LO, HI, STOP,
)
from make_start_to_data_v23 import SC, BLR, NOP

OSINIT=0x80520670
NEXT_TEXT=0x80522280


def be32(b:bytes, at:int)->int:
    return struct.unpack_from(">I", b, at)[0]


def make(owner:Path)->bytes:
    raw=owner.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=ORIGINAL_SHA:
        raise ValueError("wrong original owner Wii DOL SHA256")
    prior=make_v31(owner)
    sections=[]
    for i in range(7):
        off,guest,size=(be32(prior,base+4*i) for base in (0,0x48,0x90))
        if off<256 or size<=0 or off+size>len(prior):
            raise ValueError("invalid verified V31 section bounds")
        sections.append((guest,bytearray(prior[off:off+size])))
    if sections[1][0]!=OSINIT or sections[3][0]!=NEXT_TEXT:
        raise ValueError("inherited Wii guest memory slots changed")
    os=sections[1][1]
    if os[PREV_STOP-OSINIT:PREV_STOP-OSINIT+8]!=struct.pack(">II",SC,BLR):
        raise ValueError("V31 test-only stop missing")
    continuation=get_text(raw,PREV_STOP,STOP-PREV_STOP)
    validate_os(continuation)
    # V31's original section carries genuine PSInit and OSInit. Extend it
    # only into the previously unmapped padding between PSInit and DCEnable,
    # preserving all old bytes and all guest addresses.
    end=LO+8-OSINIT
    if not len(os)<end<200000 or OSINIT+end>NEXT_TEXT or end&3:
        raise ValueError("unsafe MEM1 setter section extension")
    os.extend(NOP.to_bytes(4,"big")*((end-len(os))//4))
    os[PREV_STOP-OSINIT:STOP-OSINIT]=continuation
    os[STOP-OSINIT:STOP-OSINIT+8]=struct.pack(">II",SC,BLR)
    for guest in (HI,LO):
        body=get_text(raw,guest,8)
        validate_setter(body,guest)
        offset=guest-OSINIT
        if os[offset:offset+8]!=NOP.to_bytes(4,"big")*2:
            raise ValueError("original MEM1 setter slot overlaps existing code")
        os[offset:offset+8]=body
    sections[1]=(OSINIT,os)
    data_off,data_size=be32(prior,0x1c),be32(prior,0xac)
    if data_off<256 or data_size!=0xB0 or data_off+data_size>len(prior):
        raise ValueError("original low-memory BSS/data relocation table changed")
    data=prior[data_off:data_off+data_size]
    output=bytearray(256+sum((len(v)+3)&~3 for _,v in sections)+len(data))
    pos=256
    for i,(guest,payload) in enumerate(sections):
        for field,value in ((0,pos),(0x48,guest),(0x90,len(payload))):
            struct.pack_into(">I",output,field+4*i,value)
        output[pos:pos+len(payload)]=payload
        pos+=(len(payload)+3)&~3
    for field,value in ((0x1c,pos),(0x64,0x80006420),(0xac,len(data))):
        struct.pack_into(">I",output,field,value)
    output[pos:pos+len(data)]=data
    struct.pack_into(">I",output,0xE0,0x8000403C)
    return bytes(output)


def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_original_dol",type=Path)
    p.add_argument("private_output_dol",type=Path)
    a=p.parse_args()
    if a.private_output_dol.exists() or a.private_output_dol.is_symlink():
        p.error("refusing owner DOL output overwrite")
    a.private_output_dol.write_bytes(make(a.private_original_dol))
    print("PASS: V32 continuous genuine MEM1 arena PowerPC fixture created privately")


if __name__=="__main__":
    main()
