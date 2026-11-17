#!/usr/bin/env python3
"""Owner-only V37 continuous Wii exception-template clearing geometry tests."""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import struct

from make_start_to_vectorclear_v37 import (
    STOP,FIRST_ORIGINAL,FIRST_DEBUG,SECOND_DEBUG,word
)
from make_start_to_exception_v35 import ENTRY,EXC_DEBUG_STOP,EXC_SOURCE_WORD
from make_start_to_mark_v36 import MARK,MARK_LENGTH
from make_hardware_boundary_v17 import ORIGINAL_SHA,get_text
from make_start_to_data_v23 import SC,BLR


def mapped(image:bytes,i:int,pc:int,size:int)->bytes:
    off,guest,count=(word(image,k+i*4) for k in (0,0x48,0x90))
    if off<256 or size<=0 or pc<guest or pc+size>guest+count or off+count>len(image):
        raise ValueError("original Wii vector-template test outside private DOL")
    return image[off+pc-guest:off+pc-guest+size]


def verify(image:bytes,original:bytes)->None:
    if hashlib.sha256(original).hexdigest()!=ORIGINAL_SHA:
        raise ValueError("original-owner Wii DOL SHA mismatch")
    if len(image)<256 or word(image,0xe0)!=0x8000403C:
        raise ValueError("not original continuous Wii __start")
    first=bytearray(mapped(image,1,ENTRY,FIRST_ORIGINAL-ENTRY))
    expected=bytearray(get_text(original,ENTRY,FIRST_ORIGINAL-ENTRY))
    for pc in (EXC_DEBUG_STOP,EXC_DEBUG_STOP+4):
        o=pc-ENTRY
        expected[o:o+4]=struct.pack(">I",SC if pc==EXC_DEBUG_STOP else BLR)
    if first!=expected:
        raise ValueError("V35/V36 original exception prefix changed")
    loop=bytearray(mapped(image,1,FIRST_ORIGINAL,STOP-FIRST_ORIGINAL))
    owner=bytearray(get_text(original,FIRST_ORIGINAL,STOP-FIRST_ORIGINAL))
    for site in (FIRST_DEBUG,SECOND_DEBUG):
        owner[site-FIRST_ORIGINAL:site-FIRST_ORIGINAL+4]=struct.pack(">I",SC)
    if loop!=owner:
        raise ValueError("original PowerPC template clear loop/guards changed")
    for site in (FIRST_DEBUG,SECOND_DEBUG):
        if mapped(image,1,site,4)!=struct.pack(">I",SC):
            raise ValueError("exception debug service is not guarded")
    for site in (STOP,EXC_DEBUG_STOP,0x805208AC):
        if mapped(image,1,site,8)!=struct.pack(">II",SC,BLR):
            raise ValueError("exception copy/systemcall/DBPrintf boundary changed")
    if mapped(image,6,MARK,MARK_LENGTH)!=get_text(original,MARK,MARK_LENGTH):
        raise ValueError("authentic original debug mark helper corrupted")
    if mapped(image,1,EXC_SOURCE_WORD,4)!=get_text(original,EXC_SOURCE_WORD,4):
        raise ValueError("original exception template source literal changed")
    regions=[]
    for i in range(7):
        off,guest,count=(word(image,k+4*i) for k in (0,0x48,0x90))
        if off<256 or count<4 or off+count>len(image) or guest&3:
            raise ValueError("private native Wii DOL text geometry malformed")
        for low,high in regions:
            if not(guest>=high or guest+count<=low):
                raise ValueError("private Wii executable guest section overlap")
        regions.append((guest,guest+count))
    off,guest,count=(word(image,k) for k in (0x1c,0x64,0xac))
    if off<256 or guest!=0x80006420 or count!=0xb0 or off+count>len(image):
        raise ValueError("original Wii startup relocation table corrupted")


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_dol",type=Path)
    p.add_argument("owner_original_dol",type=Path)
    a=p.parse_args()
    verify(a.private_dol.read_bytes(),a.owner_original_dol.read_bytes())
    print("PASS: V37 private authentic exception loop and exact syscall guard geometry")
