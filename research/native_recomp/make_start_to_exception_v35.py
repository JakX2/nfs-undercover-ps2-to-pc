#!/usr/bin/env python3
"""V35 private genuine Wii __start -> OSExceptionInit fast-path native fixture.

Only source-independent metadata and construction logic live in Git.
The actual Wii PPC words, literal pool data and generated translated C++
are extracted from a SHA-pinned owner DOL into private temporary storage.
"""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import struct

from make_start_to_ipc_v34 import make as make_v34, OSINIT, word
from make_osinit_exception_v39 import (
    ENTRY,EXC_DEBUG_STOP,EXC_NORMAL_STOP,NEXT_OS_STOP,EXC_SOURCE_WORD
)
from make_hardware_boundary_v17 import ORIGINAL_SHA,get_text,linked_target
from make_start_to_data_v23 import SC,BLR,NOP

CALL=0x805208A8
STOP=EXC_NORMAL_STOP
DEBUG_STOP=EXC_DEBUG_STOP
SAVE20=0x805450E8
DBG=0x804E50B8
EXC_GUARDS=(0x80520E98,0x80520E9C,0x80520EC0,0x80520F58)
EXC_RET_GUARDS=(0x80520EA0,0x80520EC4,0x80520F5C)


def make(owner:Path)->bytes:
    original=owner.read_bytes()
    if hashlib.sha256(original).hexdigest()!=ORIGINAL_SHA:
        raise ValueError("wrong original owner Wii DOL hash")
    previous=make_v34(owner)
    sections=[]
    for i in range(7):
        off,guest,length=(word(previous,base+4*i) for base in (0,0x48,0x90))
        if off<256 or length<=0 or off+length>len(previous):
            raise ValueError("invalid original continuous V34 DOL layout")
        sections.append((guest,bytearray(previous[off:off+length])))
    if sections[1][0]!=OSINIT:
        raise ValueError("original OSInit section no longer mapped")
    os=sections[1][1]
    at=CALL-OSINIT
    if os[at:at+8]!=struct.pack(">II",SC,BLR):
        raise ValueError("original V34 IPC->exception test boundary missing")
    call=get_text(original,CALL,4)
    if linked_target(word(call,0),CALL)!=ENTRY:
        raise ValueError("original OSExceptionInit direct call target changed")
    prefix=get_text(original,ENTRY,STOP-ENTRY)
    if len(prefix)!=180 or word(prefix,0)!=0x9421FFC0:
        raise ValueError("original Wii OSExceptionInit prologue changed")
    if (linked_target(word(prefix,16),ENTRY+16)!=SAVE20 or
        linked_target(word(prefix,DEBUG_STOP-ENTRY),DEBUG_STOP)!=DBG or
        word(prefix,0x44)!=0x4082004C or
        word(prefix,len(prefix)-4)!=0x3EC08052):
        raise ValueError("authentic exception helper, branch or source changed")
    # The helper's own literal pool is privately supplied to the native MMU
    # by the semantic test, rather than fabricated or copied to Git.
    literal=get_text(original,EXC_SOURCE_WORD,4)

    os[at:at+4]=call
    os[NEXT_OS_STOP-OSINIT:NEXT_OS_STOP-OSINIT+8]=struct.pack(">II",SC,BLR)
    at=ENTRY-OSINIT
    if os[at:at+len(prefix)]!=NOP.to_bytes(4,"big")*(len(prefix)//4):
        raise ValueError("exception prologue overlaps previously extracted code")
    os[at:at+len(prefix)]=prefix
    os[DEBUG_STOP-OSINIT:DEBUG_STOP-OSINIT+8]=struct.pack(">II",SC,BLR)
    os[STOP-OSINIT:STOP-OSINIT+8]=struct.pack(">II",SC,BLR)
    if os[EXC_SOURCE_WORD-OSINIT:EXC_SOURCE_WORD-OSINIT+4]!=NOP.to_bytes(4,"big"):
        raise ValueError("exception template literal slot unexpectedly occupied")
    os[EXC_SOURCE_WORD-OSINIT:EXC_SOURCE_WORD-OSINIT+4]=literal

    # NWiiAnalyzer may conservatively infer these immediate-operand words as
    # function roots. Stop every unknown test-only target fail-closed.
    for address in EXC_GUARDS:
        off=address-OSINIT
        if os[off:off+4]!=NOP.to_bytes(4,"big"):
            raise ValueError("exception synthetic root-guard overlaps real code")
        struct.pack_into(">I",os,off,SC)
    for address in EXC_RET_GUARDS:
        off=address-OSINIT
        if os[off:off+4]!=NOP.to_bytes(4,"big"):
            raise ValueError("exception guarded return overlaps real code")
        struct.pack_into(">I",os,off,BLR)
    sections[1]=(OSINIT,os)

    data_off,data_size=word(previous,0x1c),word(previous,0xac)
    if data_off<256 or data_size!=0xb0 or data_off+data_size>len(previous):
        raise ValueError("original game relocator data table changed")
    data=previous[data_off:data_off+data_size]
    out=bytearray(256+sum((len(blob)+3)&~3 for _,blob in sections)+len(data))
    pos=256
    for i,(guest,blob) in enumerate(sections):
        for header,value in ((0,pos),(0x48,guest),(0x90,len(blob))):
            struct.pack_into(">I",out,header+4*i,value)
        out[pos:pos+len(blob)]=blob
        pos+=(len(blob)+3)&~3
    for header,value in ((0x1c,pos),(0x64,0x80006420),(0xac,len(data))):
        struct.pack_into(">I",out,header,value)
    out[pos:pos+len(data)]=data
    struct.pack_into(">I",out,0xe0,0x8000403C)
    return bytes(out)


def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("original_owner_dol",type=Path)
    p.add_argument("private_output_dol",type=Path)
    a=p.parse_args()
    if a.private_output_dol.exists() or a.private_output_dol.is_symlink():
        p.error("refusing overwrite of private Wii image")
    a.private_output_dol.write_bytes(make(a.original_owner_dol))
    print("PASS: original Wii V35 continuous bounded exception prologue generated privately")


if __name__=="__main__":
    main()
