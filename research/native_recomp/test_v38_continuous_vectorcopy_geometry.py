#!/usr/bin/env python3
"""Strict private original-Wii V38 vector memcpy/DOL boundary verifier."""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import struct

from make_start_to_vectorcopy_v38 import (
    STOP,COPY_START,COPY_CALL,CACHE_FUNC,MEMCPY,TEMPLATE_SRC,
    TEMPLATE_SIZE,PRIVATE_DATA_GUEST,word
)
from make_start_to_vectorclear_v37 import FIRST_ORIGINAL,FIRST_DEBUG,SECOND_DEBUG
from make_start_to_exception_v35 import ENTRY,EXC_DEBUG_STOP,EXC_SOURCE_WORD
from make_start_to_mark_v36 import MARK,MARK_LENGTH
from make_hardware_boundary_v17 import ORIGINAL_SHA,get_text,linked_target
from make_start_to_data_v23 import SC,BLR


def mapped(image:bytes,i:int,pc:int,size:int,is_data:bool=False)->bytes:
    bases=(0x1c,0x64,0xac) if is_data else (0,0x48,0x90)
    off,guest,count=(word(image,k+i*4) for k in bases)
    if off<256 or size<=0 or pc<guest or pc+size>guest+count or off+count>len(image):
        raise ValueError("original Wii fixture span outside private DOL section")
    return image[off+pc-guest:off+pc-guest+size]


def verify(image:bytes,original:bytes)->None:
    if hashlib.sha256(original).hexdigest()!=ORIGINAL_SHA:
        raise ValueError("original-owner Wii DOL SHA256 mismatch")
    if len(image)<256 or word(image,0xe0)!=0x8000403C:
        raise ValueError("incorrect original Wii continuous __start guest entry")
    prefix=bytearray(mapped(image,1,ENTRY,FIRST_ORIGINAL-ENTRY))
    expected=bytearray(get_text(original,ENTRY,FIRST_ORIGINAL-ENTRY))
    for site in (EXC_DEBUG_STOP,EXC_DEBUG_STOP+4):
        at=site-ENTRY
        expected[at:at+4]=struct.pack(">I",SC if site==EXC_DEBUG_STOP else BLR)
    if prefix!=expected:
        raise ValueError("previous original exception prologue changed")
    code=bytearray(mapped(image,1,FIRST_ORIGINAL,STOP-FIRST_ORIGINAL))
    owner=bytearray(get_text(original,FIRST_ORIGINAL,STOP-FIRST_ORIGINAL))
    for site in (FIRST_DEBUG,SECOND_DEBUG):
        owner[site-FIRST_ORIGINAL:site-FIRST_ORIGINAL+4]=struct.pack(">I",SC)
    if code!=owner:
        raise ValueError("owner-original vector copying/clearing PPC span mutated")
    for site in (FIRST_DEBUG,SECOND_DEBUG):
        if mapped(image,1,site,4)!=struct.pack(">I",SC):
            raise ValueError("original unimplemented debug branch lacks terminal guard")
    for site in (STOP,EXC_DEBUG_STOP,0x805208AC):
        if mapped(image,1,site,8)!=struct.pack(">II",SC,BLR):
            raise ValueError("private exact guest-PC syscall stop changed")
    if mapped(image,1,COPY_CALL,4)!=get_text(original,COPY_CALL,4):
        raise ValueError("original exception vector memcpy BL changed")
    if linked_target(word(mapped(image,1,COPY_CALL,4),0),COPY_CALL)!=MEMCPY:
        raise ValueError("original Wii memcpy return call target changed")
    if linked_target(word(get_text(original,STOP,4),0),STOP)!=CACHE_FUNC:
        raise ValueError("next original cache flush service call target changed")
    if mapped(image,6,MARK,MARK_LENGTH)!=get_text(original,MARK,MARK_LENGTH):
        raise ValueError("original exception mark helper mutated")
    if mapped(image,1,EXC_SOURCE_WORD,4)!=get_text(original,EXC_SOURCE_WORD,4):
        raise ValueError("private original exception template source literal changed")
    original_handler=get_text(original,TEMPLATE_SRC,TEMPLATE_SIZE)
    if mapped(image,1,TEMPLATE_SRC,TEMPLATE_SIZE)==original_handler:
        # This would be surprising because the upstream native analyzer
        # requires strict test-only guards in this region.
        raise ValueError("original template unexpectedly unguarded in native executable section")
    if mapped(image,1,0x80520EC0,4)!=struct.pack(">I",SC):
        raise ValueError("required synthetic PPC conservative-analyzer stop missing")
    if mapped(image,1,0x80520EC4,4)!=struct.pack(">I",BLR):
        raise ValueError("required synthetic PPC conservative-analyzer return missing")
    if mapped(image,1,0x80520F58,4)!=struct.pack(">I",SC):
        raise ValueError("last conservative-analyzer stop missing")
    if mapped(image,1,0x80520F5C,4)!=struct.pack(">I",BLR):
        raise ValueError("last conservative-analyzer return missing")

    regions=[]
    for i in range(7):
        off,guest,n=(word(image,k+i*4) for k in (0,0x48,0x90))
        if off<256 or n<4 or guest&3 or off+n>len(image):
            raise ValueError("malformed original Wii text geometry")
        for other_off,other_end,other_guest,other_end_guest in regions:
            if not(off>=other_end or off+n<=other_off):
                raise ValueError("overlapping private Wii code file sections")
            if not(guest>=other_end_guest or guest+n<=other_guest):
                raise ValueError("overlapping private Wii guest text")
        regions.append((off,off+n,guest,guest+n))
    data_spans=[]
    for i in range(2):
        off,guest,n=(word(image,k+i*4) for k in (0x1c,0x64,0xac))
        if off<256 or n<4 or off+n>len(image) or off&3 or guest&3:
            raise ValueError("malformed private Wii fixture data section")
        for a,b,g,h in regions+data_spans:
            if not(off>=b or off+n<=a) or not(guest>=h or guest+n<=g):
                raise ValueError("data and code mappings overlap")
        data_spans.append((off,off+n,guest,guest+n))
    if (word(image,0x64)!=0x80006420 or word(image,0xac)!=0xB0 or
        word(image,0x68)!=PRIVATE_DATA_GUEST or word(image,0xb0)!=TEMPLATE_SIZE):
        raise ValueError("original startup relocator / private handler oracle layout changed")
    if mapped(image,1,PRIVATE_DATA_GUEST,TEMPLATE_SIZE,is_data=True)!=original_handler:
        raise ValueError("original-owner 152-byte handler template oracle mutated")
    for i in range(2,11):
        if any(word(image,k+i*4) for k in (0x1c,0x64,0xac)):
            raise ValueError("unexpected additional original Wii DOL data section")


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("private_test_dol",type=Path)
    parser.add_argument("private_original_dol",type=Path)
    a=parser.parse_args()
    verify(a.private_test_dol.read_bytes(),a.private_original_dol.read_bytes())
    print("PASS: original Wii V38 private vector-copy/handler/relocator geometry verified")
