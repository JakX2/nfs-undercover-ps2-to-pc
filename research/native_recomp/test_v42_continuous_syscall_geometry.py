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
    previous=make_v41(owner) # SHA-authenticated owner and full V41 original PPC
    if len(actual)!=len(previous) or actual[:256]!=previous[:256] or word(actual,0xE0)!=START:
        raise ValueError("V42 altered original DOL length, entry or section metadata")
    def mapped(pc:int,n:int)->int:
        matches=[]
        for i in range(7):
            off,base,size=(word(actual,k+4*i) for k in (0,0x48,0x90))
            if base<=pc and pc+n<=base+size:
                if off<256 or off+size>len(actual):
                    raise ValueError("V42 private text image section out of bounds")
                matches.append(off+pc-base)
        if len(matches)!=1:
            raise ValueError("V42 syscall guest code lacks unique text segment")
        return matches[0]
    old_at=mapped(OLD_STOP,12)
    source_at=mapped(SOURCE,END-SOURCE)
    allowed=set(range(old_at,old_at+12))
    allowed.update(range(source_at,source_at+END-SOURCE))
    for pos,(old,new) in enumerate(zip(previous,actual)):
        if pos not in allowed and old!=new:
            raise ValueError("V42 modified earlier verified startup/owner oracle bytes")
    if actual[old_at:old_at+4]!=text_at(owner.read_bytes(),OLD_STOP,4):
        raise ValueError("V42 OSInit native syscall BL differs from pinned owner")
    if actual[old_at+4:old_at+12]!=struct.pack(">II",SC,BLR):
        raise ValueError("V42 next original OSInit service not bounded")
    if actual[source_at:source_at+END-SOURCE]!=text_at(owner.read_bytes(),SOURCE,END-SOURCE):
        raise ValueError("V42 genuine __OSInitSystemCall code differs from pinned owner")
    if previous[source_at:source_at+END-SOURCE]!=struct.pack(">I",NOP)*((END-SOURCE)//4):
        raise ValueError("V42 original syscall mapped over existing PPC fixture")

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_fixture",type=Path)
    p.add_argument("owner_original_dol",type=Path)
    a=p.parse_args()
    verify(a.private_fixture.read_bytes(),a.owner_original_dol)
    print("PASS: original Wii V42 syscall instructions, guards and no-overwrite geometry")
