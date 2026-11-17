#!/usr/bin/env python3
"""V35 owner-only original Wii exception fast-path geometry/safety validator."""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import struct

from make_start_to_exception_v35 import (
    CALL, STOP, DEBUG_STOP, ENTRY, EXC_SOURCE_WORD,
    EXC_GUARDS, EXC_RET_GUARDS, word
)
from make_hardware_boundary_v17 import ORIGINAL_SHA,get_text,linked_target
from make_start_to_data_v23 import SC,BLR


def mapped(image:bytes,index:int,pc:int,length:int)->bytes:
    off,guest,size=(word(image,k+index*4) for k in (0,0x48,0x90))
    if off<256 or length<=0 or pc<guest or pc+length>guest+size or off+size>len(image):
        raise ValueError("private Wii native exception test DOL section out of bounds")
    return image[off+pc-guest:off+pc-guest+length]


def verify(image:bytes,original:bytes)->None:
    if hashlib.sha256(original).hexdigest()!=ORIGINAL_SHA:
        raise ValueError("owner original DOL hash mismatch")
    if len(image)<256 or word(image,0xe0)!=0x8000403C:
        raise ValueError("wrong original __start entry")
    call=mapped(image,1,CALL,4)
    if call!=get_text(original,CALL,4) or linked_target(word(call,0),CALL)!=ENTRY:
        raise ValueError("original OSExceptionInit callsite changed")
    prefix=bytearray(mapped(image,1,ENTRY,STOP-ENTRY))
    expected=bytearray(get_text(original,ENTRY,STOP-ENTRY))
    for addr in (DEBUG_STOP,DEBUG_STOP+4):
        off=addr-ENTRY
        expected[off:off+4]=struct.pack(">I",SC if addr==DEBUG_STOP else BLR)
    if prefix!=expected:
        raise ValueError("non-boundary authentic Wii exception PPC code changed")
    for pc in (STOP,DEBUG_STOP,CALL+4):
        if mapped(image,1,pc,8)!=struct.pack(">II",SC,BLR):
            raise ValueError("Wii exception test-only guarded stop or return missing")
    if mapped(image,1,EXC_SOURCE_WORD,4)!=get_text(original,EXC_SOURCE_WORD,4):
        raise ValueError("original exception template literal changed")
    for pc in EXC_GUARDS:
        if mapped(image,1,pc,4)!=struct.pack(">I",SC):
            raise ValueError("unguarded conservative analyzer root")
    for pc in EXC_RET_GUARDS:
        if mapped(image,1,pc,4)!=struct.pack(">I",BLR):
            raise ValueError("unguarded synthetic analyzer return")
    mapped(image,5,0x8052AE80,24)
    spans=[]
    for i in range(7):
        off,guest,n=(word(image,k+i*4) for k in (0,0x48,0x90))
        if off<256 or n<4 or off+n>len(image) or guest&3:
            raise ValueError("unsafe private Wii code section")
        for a,b in spans:
            if not(guest>=b or guest+n<=a):
                raise ValueError("overlapping original guest code sections")
        spans.append((guest,guest+n))
    off,guest,n=(word(image,k) for k in (0x1c,0x64,0xac))
    if off<256 or guest!=0x80006420 or n!=0xb0 or off+n>len(image):
        raise ValueError("original Wii BSS relocator table missing")


def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_dol",type=Path)
    p.add_argument("original_owner_dol",type=Path)
    a=p.parse_args()
    verify(a.private_dol.read_bytes(),a.original_owner_dol.read_bytes())
    print("PASS: original V35 continuous bounded exception code/guards/stop geometry")


if __name__=="__main__":
    main()
