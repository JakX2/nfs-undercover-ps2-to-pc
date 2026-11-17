#!/usr/bin/env python3
"""Owner-private V36 genuine exception marker and DOL section geometry guards."""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import struct

from make_start_to_mark_v36 import OSINIT, MARK, MARK_LENGTH, STOP, MARK_FIRST, PREVIOUS_STOP, word
from make_start_to_exception_v35 import ENTRY, EXC_DEBUG_STOP, EXC_SOURCE_WORD
from make_hardware_boundary_v17 import ORIGINAL_SHA, get_text, linked_target
from make_start_to_data_v23 import SC, BLR


def mapped(image: bytes,index:int,pc:int,count:int) -> bytes:
    off,guest,size=(word(image,k+index*4) for k in (0,0x48,0x90))
    if off<256 or count<=0 or pc<guest or pc+count>guest+size or off+size>len(image):
        raise ValueError("original bounded Wii marker outside private DOL section")
    return image[off+pc-guest:off+pc-guest+count]


def verify(image:bytes,original:bytes) -> None:
    if hashlib.sha256(original).hexdigest()!=ORIGINAL_SHA:
        raise ValueError("incorrect original-owner Wii DOL SHA256")
    if len(image)<256 or word(image,0xe0)!=0x8000403C:
        raise ValueError("not the original continuous Wii __start entry")
    prefix=bytearray(mapped(image,1,ENTRY,PREVIOUS_STOP-ENTRY))
    expected=bytearray(get_text(original,ENTRY,PREVIOUS_STOP-ENTRY))
    for pc in (EXC_DEBUG_STOP,EXC_DEBUG_STOP+4):
        pos=pc-ENTRY
        expected[pos:pos+4]=struct.pack(">I",SC if pc==EXC_DEBUG_STOP else BLR)
    if prefix!=expected:
        raise ValueError("authentic V35 original exception prelude differs")
    original_body=bytearray(get_text(original,PREVIOUS_STOP,STOP-PREVIOUS_STOP))
    first_offset=MARK_FIRST-PREVIOUS_STOP
    original_body[first_offset:first_offset+8]=struct.pack(">II",SC,BLR)
    if mapped(image,1,PREVIOUS_STOP,len(original_body))!=original_body:
        raise ValueError("original V36 exception branch or first-mark guard differs")
    for pc in (MARK_FIRST,STOP,EXC_DEBUG_STOP,0x805208AC):
        if mapped(image,1,pc,8)!=struct.pack(">II",SC,BLR):
            raise ValueError("unverified exception path not safely guarded")
    for site in (0x80520CC4,0x80520CF0):
        ins=mapped(image,1,site,4)
        if ins!=get_text(original,site,4) or linked_target(word(ins,0),site)!=MARK:
            raise ValueError("original exception marker BL callsite differs")
    helper=mapped(image,6,MARK,MARK_LENGTH)
    if helper!=get_text(original,MARK,MARK_LENGTH) or word(helper,20)!=BLR:
        raise ValueError("authentic __DBIsExceptionMarked body mutated")
    if mapped(image,1,EXC_SOURCE_WORD,4)!=get_text(original,EXC_SOURCE_WORD,4):
        raise ValueError("original exception-template source word differs")
    ranges=[]
    for i in range(7):
        off,guest,size=(word(image,k+i*4) for k in (0,0x48,0x90))
        if off<256 or size<4 or off+size>len(image) or guest&3:
            raise ValueError("owner Wii DOL code section invalid")
        for lo,hi in ranges:
            if not (guest>=hi or guest+size<=lo):
                raise ValueError("overlapping original Wii guest code sections")
        ranges.append((guest,guest+size))
    off,guest,size=(word(image,k) for k in (0x1c,0x64,0xac))
    if off<256 or guest!=0x80006420 or size!=0xb0 or off+size>len(image):
        raise ValueError("original Wii startup data relocation section changed")


def main()->None:
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("private_dol",type=Path)
    cli.add_argument("original_owner_dol",type=Path)
    args=cli.parse_args()
    verify(args.private_dol.read_bytes(),args.original_owner_dol.read_bytes())
    print("PASS: authentic original V36 continuous marker PPC and private geometry")


if __name__=="__main__":
    main()
