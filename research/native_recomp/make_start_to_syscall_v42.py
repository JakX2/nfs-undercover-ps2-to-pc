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
    # In the continuous __start image, the existing cache/IPC text section
    # already spans SOURCE and GETTIME. Do not prepend a separate section:
    # that would overlap a verified DOL guest-memory mapping.
    image=bytearray(prior)
    def mapped(pc:int,n:int)->int:
        matches=[]
        for i in range(7):
            off,base,length=(word(image,k+4*i) for k in (0,0x48,0x90))
            if base<=pc and pc+n<=base+length:
                if off<256 or off+length>len(image):
                    raise ValueError("V42 original text section bounds differ")
                matches.append(off+pc-base)
        if len(matches)!=1:
            raise ValueError("V42 PPC instruction range ambiguously mapped")
        return matches[0]
    at=mapped(OLD_STOP,12)
    if image[at:at+8]!=struct.pack(">II",SC,BLR) or word(image,at+8)!=NOP:
        raise ValueError("V41 original OSInit syscall checkpoint changed")
    call=text_at(raw,OLD_STOP,4)
    if target(word(call,0),OLD_STOP,True)!=ENTRY:
        raise ValueError("original __OSInitSystemCall OSInit BL target changed")
    image[at:at+4]=call
    image[at+4:at+12]=struct.pack(">II",SC,BLR)

    code=text_at(raw,SOURCE,END-SOURCE)
    if len(code)!=0x80 or word(code,ENTRY-SOURCE)!=0x9421FFF0 or word(code,END-SOURCE-4)!=BLR:
        raise ValueError("original Wii syscall initializer body incomplete")
    for pc,dest in ((ENTRY+0x2C,COPY),(ENTRY+0x38,FLUSH),(ENTRY+0x48,INVALIDATE)):
        if target(word(code,pc-SOURCE),pc,True)!=dest:
            raise ValueError("original syscall helper BL destination changed")
    if word(code,ENTRY+0x34-SOURCE)!=0x38800100 or word(code,ENTRY+0x44-SOURCE)!=0x38800100:
        raise ValueError("original Wii syscall cache range differs")
    if word(code,ENTRY+0x28-SOURCE)>>26!=31:
        raise ValueError("original Wii syscall handler copy length changed")
    off=mapped(SOURCE,len(code))
    if image[off:off+len(code)]!=struct.pack(">I",NOP)*(len(code)//4):
        raise ValueError("original syscall PPC overlaps inherited native startup")
    if not any(base<=GETTIME and GETTIME+24<=base+len(body) and
               base<=SOURCE and END<=base+len(body) for base,body in sections_of(prior)[0]):
        raise ValueError("existing continuous GETTIME/syscall section geometry differs")
    image[off:off+len(code)]=code
    out=bytes(image)
    if word(out,0xE0)!=START:
        raise ValueError("V42 original Wii __start entry changed")
    return out

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("owner_original_dol",type=Path)
    p.add_argument("private_fixture",type=Path)
    a=p.parse_args()
    if a.private_fixture.exists() or a.private_fixture.is_symlink():
        p.error("refusing to overwrite owner-private test fixture")
    a.private_fixture.write_bytes(make(a.owner_original_dol))
    print("PASS: original Wii V42 continuous syscall initializer fixture built privately")
