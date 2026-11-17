#!/usr/bin/env python3
"""V42 owner-private continuous Wii __start -> original __OSInitSystemCall.

Copies the SHA-pinned original PowerPC syscall initializer/callsite into the
native test image. All original bytes and recompilation products stay in
private temporary storage. The next OSInit call remains a synthetic stop.
"""
from __future__ import annotations
import argparse
import struct
from pathlib import Path
from make_start_to_epilogue_v41 import make as make_v41, sections_of
from make_start_to_vectorcopy_v38 import word
from make_osinit_execparams_v28 import text_at, target, SC, BLR, NOP
from make_osinit_systemcall_v45 import SOURCE,ENTRY,END,FLUSH,INVALIDATE,COPY

OSINIT=0x80520670
GETTIME=0x8052A824
OLD_STOP=0x805208AC
STOP=0x805208B0
START=0x8000403C
DEST=0x80000C00

def make(owner:Path)->bytes:
    prior=make_v41(owner) # transitive owner SHA, original helper and DOL integrity
    raw=owner.read_bytes()
    text,data=sections_of(prior)
    osidx=[i for i,(g,_) in enumerate(text) if g==OSINIT]
    timeidx=[i for i,(g,_) in enumerate(text) if g==GETTIME]
    if len(osidx)!=1 or len(timeidx)!=1:
        raise ValueError("V42 original OSInit/time DOL section mapping changed")
    osbase,os=text[osidx[0]]
    at=OLD_STOP-osbase
    if os[at:at+8]!=struct.pack(">II",SC,BLR) or word(os,at+8)!=NOP:
        raise ValueError("V41 OSInit synthetic checkpoint was modified")
    call=text_at(raw,OLD_STOP,4)
    if target(word(call,0),OLD_STOP,True)!=ENTRY:
        raise ValueError("original OSInit __OSInitSystemCall call graph changed")
    os[at:at+4]=call
    os[at+4:at+12]=struct.pack(">II",SC,BLR)
    text[osidx[0]]=(osbase,os)

    # Keep the exact owner source at original guest PCs. Only the unused
    # address gap before inherited GETTIME is synthesized with inert NOPs.
    code=text_at(raw,SOURCE,END-SOURCE)
    if len(code)!=0x80 or word(code,ENTRY-SOURCE)!=0x9421FFF0 or word(code,END-SOURCE-4)!=BLR:
        raise ValueError("original Wii syscall installer body incomplete")
    for pc,dest in ((ENTRY+0x2C,COPY),(ENTRY+0x38,FLUSH),(ENTRY+0x48,INVALIDATE)):
        if target(word(code,pc-SOURCE),pc,True)!=dest:
            raise ValueError("original syscall helper call target changed")
    if word(code,ENTRY+0x34-SOURCE)!=0x38800100 or word(code,ENTRY+0x44-SOURCE)!=0x38800100:
        raise ValueError("original syscall cache operation size changed")
    if word(code,ENTRY+0x28-SOURCE)>>26!=31:
        raise ValueError("original syscall source-copy length arithmetic changed")
    gap=GETTIME-SOURCE
    if gap<len(code) or gap%4 or gap>0x2000:
        raise ValueError("original syscall image not safely bounded before GETTIME")
    prefix=bytearray(struct.pack(">I",NOP)*(gap//4))
    prefix[:len(code)]=code
    old_time=text[timeidx[0]][1]
    text[timeidx[0]]=(SOURCE,prefix+old_time)
    for i,(guest,body) in enumerate(text):
        if i!=timeidx[0] and guest<SOURCE+len(prefix)+len(old_time) and guest+len(body)>SOURCE:
            raise ValueError("syscall code section overlaps existing original Wii text")

    out=bytearray(prior[:256])
    for i,(guest,body) in enumerate(text):
        off=len(out)
        for base,value in ((0,off),(0x48,guest),(0x90,len(body))):
            struct.pack_into(">I",out,base+4*i,value)
        out.extend(body)
        out.extend(bytes((-len(out))%4))
    for i,(guest,body) in enumerate(data):
        off=len(out)
        for base,value in ((0x1c,off),(0x64,guest),(0xac,len(body))):
            struct.pack_into(">I",out,base+4*i,value)
        out.extend(body)
        out.extend(bytes((-len(out))%4))
    if word(out,0xE0)!=START:
        raise ValueError("V42 original Wii __start entry changed")
    return bytes(out)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("owner_original_dol",type=Path)
    p.add_argument("private_fixture",type=Path)
    a=p.parse_args()
    if a.private_fixture.exists() or a.private_fixture.is_symlink():
        p.error("refusing to overwrite owner-private test fixture")
    a.private_fixture.write_bytes(make(a.owner_original_dol))
    print("PASS: original Wii V42 continuous syscall initializer fixture built privately")
