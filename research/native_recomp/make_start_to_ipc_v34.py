#!/usr/bin/env python3
"""Private Wii V34 continuous original __start through __OSInitIPCBuffer.

Stitches the authentic Wii OSInit BL and complete original 24-byte IPC-buffer
helper from the SHA-256-pinned owner DOL. The game-derived bytes and generated
C++ exist only in runner scratch. The host IOS IPC subsystem is NOT emulated.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import hashlib
import struct

from make_start_to_mem2_v33 import make as make_v33, word
from make_osinit_ipc_v38 import validate_ipc, IPC
from make_hardware_boundary_v17 import ORIGINAL_SHA,get_text,linked_target
from make_start_to_data_v23 import SC,BLR,NOP

CALL=0x805208A4
STOP=0x805208A8
OSINIT=0x80520670
CACHE=0x80522540


def make(owner:Path)->bytes:
    source=owner.read_bytes()
    if hashlib.sha256(source).hexdigest()!=ORIGINAL_SHA:
        raise ValueError("owner Wii DOL SHA-256 mismatch")
    previous=make_v33(owner)
    sections=[]
    for i in range(7):
        off,guest,size=(word(previous,k+i*4) for k in (0,0x48,0x90))
        if off<256 or size<4 or off+size>len(previous):
            raise ValueError("V33 DOL code section bounds are not valid")
        sections.append((guest,bytearray(previous[off:off+size])))
    if sections[1][0]!=OSINIT or sections[5][0]!=CACHE:
        raise ValueError("inherited guest OSInit/cache sections moved")
    os=sections[1][1]
    at=CALL-OSINIT
    if os[at:at+8]!=struct.pack(">II",SC,BLR):
        raise ValueError("V33 terminal test stop missing")
    call=get_text(source,CALL,4)
    if linked_target(word(call,0),CALL)!=IPC:
        raise ValueError("original __OSInitIPCBuffer BL call target changed")
    os[at:at+4]=call
    os[STOP-OSINIT:STOP-OSINIT+8]=struct.pack(">II",SC,BLR)
    sections[1]=(OSINIT,os)

    ipc=get_text(source,IPC,24)
    validate_ipc(ipc)
    cache=sections[5][1]
    off=IPC-CACHE
    if off<0 or off+len(ipc)>len(cache):
        raise ValueError("original IPC function outside bounded original helper section")
    if cache[off:off+24]!=NOP.to_bytes(4,"big")*6:
        raise ValueError("IPC insertion overlaps previously used guest function")
    cache[off:off+24]=ipc
    sections[5]=(CACHE,cache)

    data_off,data_size=word(previous,0x1c),word(previous,0xac)
    if data_off<256 or data_size!=0xB0 or data_off+data_size>len(previous):
        raise ValueError("original startup data table invalid")
    data=previous[data_off:data_off+data_size]
    result=bytearray(256+sum((len(part)+3)&~3 for _,part in sections)+len(data))
    pos=256
    for i,(guest,part) in enumerate(sections):
        for k,v in ((0,pos),(0x48,guest),(0x90,len(part))):
            struct.pack_into(">I",result,k+4*i,v)
        result[pos:pos+len(part)]=part
        pos+=(len(part)+3)&~3
    for k,v in ((0x1c,pos),(0x64,0x80006420),(0xac,len(data))):
        struct.pack_into(">I",result,k,v)
    result[pos:pos+len(data)]=data
    struct.pack_into(">I",result,0xe0,0x8000403C)
    return bytes(result)


def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_original_dol",type=Path)
    p.add_argument("private_output_dol",type=Path)
    args=p.parse_args()
    if args.private_output_dol.exists() or args.private_output_dol.is_symlink():
        p.error("refusing to overwrite private original image")
    args.private_output_dol.write_bytes(make(args.private_original_dol))
    print("PASS: original Wii V34 continuous IPC-buffer native test image created privately")


if __name__=="__main__":
    main()
