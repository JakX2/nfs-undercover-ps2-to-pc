#!/usr/bin/env python3
"""Privacy-safe V42 original syscall PowerPC, section and no-overwrite guards."""
from __future__ import annotations
import argparse
from pathlib import Path
import struct
from make_start_to_epilogue_v41 import make as make_v41,sections_of
from make_start_to_syscall_v42 import (
    SOURCE,END,GETTIME,OLD_STOP,STOP,OSINIT,START
)
from make_start_to_vectorcopy_v38 import word
from make_osinit_execparams_v28 import text_at,SC,BLR,NOP

def verify(actual:bytes,owner:Path)->None:
    previous=make_v41(owner) # owner SHA + full native V41 fixture geometry
    if len(actual)<256 or word(actual,0xE0)!=START:
        raise ValueError("V42 original entry or DOL header truncated")
    mutable=set(range(7*4))|set(range(0x90,0x90+7*4))
    mutable.update(range(0x1c,0x1c+2*4))
    mutable.update(range(0x48,0x48+7*4)) # GETTIME -> original syscall source
    for pos in range(256):
        if pos not in mutable and actual[pos]!=previous[pos]:
            raise ValueError("V42 unexpected game DOL header change")
    oldtext,olddata=sections_of(previous)
    newtext,newdata=sections_of(actual)
    if olddata!=newdata:
        raise ValueError("V42 original startup table or handler oracle modified")
    if len(oldtext)!=len(newtext) or len(newtext)!=7:
        raise ValueError("V42 changed guest text section count")
    for (base,old),(guest,new) in zip(oldtext,newtext):
        if base==OSINIT:
            if guest!=base or len(new)!=len(old):
                raise ValueError("V42 OSInit text geometry changed")
            off=OLD_STOP-base
            if new[:off]!=old[:off] or new[off+12:]!=old[off+12:]:
                raise ValueError("V42 overwrote previous continuous OSInit code")
            if new[off:off+4]!=text_at(owner.read_bytes(),OLD_STOP,4):
                raise ValueError("V42 original __OSInitSystemCall BL differs")
            if new[off+4:off+12]!=struct.pack(">II",SC,BLR):
                raise ValueError("V42 next-original-service synthetic stop missing")
        elif base==GETTIME:
            if guest!=SOURCE or len(new)!=(GETTIME-SOURCE)+len(old):
                raise ValueError("V42 syscall/gettime guest PC map changed")
            if new[GETTIME-SOURCE:]!=old:
                raise ValueError("V42 modified previously translated Wii GETTIME")
            if new[:END-SOURCE]!=text_at(owner.read_bytes(),SOURCE,END-SOURCE):
                raise ValueError("V42 syscall initializer instructions differ from owner")
            if new[END-SOURCE:GETTIME-SOURCE]!=struct.pack(">I",NOP)*((GETTIME-END)//4):
                raise ValueError("V42 syscall section inert gap contains unexpected code")
        elif guest!=base or new!=old:
            raise ValueError("V42 touched previously verified guest PPC or helper text")
    if len(set(x for x,_ in newtext))!=7 or word(actual,0xE0)!=START:
        raise ValueError("V42 duplicate text segment base or wrong guest entry")

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_fixture",type=Path)
    p.add_argument("owner_original_dol",type=Path)
    a=p.parse_args()
    verify(a.private_fixture.read_bytes(),a.owner_original_dol)
    print("PASS: original Wii V42 syscall instructions, guards and no-overwrite geometry")
