#!/usr/bin/env python3
"""Owner-only original Wii continuous IPC-function and test-boundary validator."""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import struct

from make_start_to_ipc_v34 import CALL,STOP,IPC,OSINIT,word
from make_osinit_ipc_v38 import validate_ipc
from make_osinit_mem2_v37 import check_source as verify_mem2
from make_hardware_boundary_v17 import ORIGINAL_SHA,get_text,linked_target
from make_start_to_data_v23 import SC,BLR


def mapped(image:bytes,index:int,pc:int,count:int)->bytes:
    offset,guest,size=(word(image,k+4*index) for k in (0,0x48,0x90))
    if offset<256 or count<=0 or pc<guest or pc+count>guest+size or offset+size>len(image):
        raise ValueError("private Wii IPC image guest code section out of bounds")
    return image[offset+pc-guest:offset+pc-guest+count]


def verify(image:bytes,original:bytes)->None:
    if hashlib.sha256(original).hexdigest()!=ORIGINAL_SHA:
        raise ValueError("incorrect owner original Wii DOL SHA-256")
    if len(image)<256 or word(image,0xe0)!=0x8000403C:
        raise ValueError("not original continuous Wii __start image")
    prior=mapped(image,1,0x80520818,CALL-0x80520818)
    verify_mem2(prior)
    if prior!=get_text(original,0x80520818,len(prior)):
        raise ValueError("original MEM2 selector mutated")
    call=mapped(image,1,CALL,4)
    if call!=get_text(original,CALL,4) or linked_target(word(call,0),CALL)!=IPC:
        raise ValueError("original IPC callsite mutated")
    body=mapped(image,5,IPC,24)
    validate_ipc(body)
    if body!=get_text(original,IPC,24):
        raise ValueError("original six-instruction IPC helper changed")
    if mapped(image,1,STOP,8)!=struct.pack(">II",SC,BLR):
        raise ValueError("original IPC return 0x805208A8 test stop missing")
    # Seven original-code sections, one original data table. Never overlap.
    regions=[]
    for i in range(7):
        offset,guest,size=(word(image,k+4*i) for k in (0,0x48,0x90))
        if offset<256 or size<4 or offset+size>len(image) or guest&3:
            raise ValueError("unbounded owner-original Wii section geometry")
        for a,b in regions:
            if not(guest>=b or guest+size<=a):
                raise ValueError("Wii guest executable sections overlap")
        regions.append((guest,guest+size))
    data_off,data_guest,data_size=(word(image,k) for k in (0x1c,0x64,0xac))
    if data_off<256 or data_guest!=0x80006420 or data_size!=0xb0 or data_off+data_size>len(image):
        raise ValueError("original Wii relocator data table not preserved")


def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_dol",type=Path)
    p.add_argument("owner_original_dol",type=Path)
    a=p.parse_args()
    verify(a.private_dol.read_bytes(),a.owner_original_dol.read_bytes())
    print("PASS: original V34 continuous IPC-buffer BL/body/stop private geometry")


if __name__=="__main__":
    main()
