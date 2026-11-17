#!/usr/bin/env python3
"""V45 fail-closed original PPC/checkpoint/no-overwrite DOL geometry oracle."""
from __future__ import annotations
import argparse
import struct
from pathlib import Path

from make_start_to_module_v44 import make as make_v44
from make_start_to_epilogue_v41 import sections_of
from make_start_to_interrupt_v45 import (
    START,OSINIT,OLD_STOP,AFTER_CALL,INTERRUPT,STOP,MEMSET,FILL,
    FILL_LENGTH,PREFIX_LENGTH)
from make_start_to_vectorcopy_v38 import word
from make_osinit_execparams_v28 import text_at,SC,BLR,NOP

def verify(image:bytes,owner:Path)->None:
    prior=make_v44(owner)  # SHA-verified all earlier original Wii startup
    if len(image)<256 or word(image,0xE0)!=START:
        raise ValueError("V45 original entry/header invalid")
    mutable=set(range(0,7*4))|set(range(0x90,0x90+7*4))
    mutable.update(range(0x1c,0x1c+2*4))
    for i in range(256):
        if i not in mutable and image[i]!=prior[i]:
            raise ValueError("V45 modified a non-relocatable DOL header byte")
    oldtext,olddata=sections_of(prior)
    newtext,newdata=sections_of(image)
    if olddata!=newdata or len(oldtext)!=7 or len(newtext)!=7:
        raise ValueError("V45 original relocator/oracle payload changed")
    allowed=((OLD_STOP,AFTER_CALL+8),(INTERRUPT,STOP+8))
    for (base,old),(new_base,new) in zip(oldtext,newtext):
        if new_base!=base or len(new)<len(old):
            raise ValueError("V45 original Wii text section rebased or truncated")
        for offset in range(len(old)):
            pc=base+offset
            if not any(a<=pc<b for a,b in allowed) and new[offset]!=old[offset]:
                raise ValueError("V45 altered previous verified original PPC")
        if len(new)!=len(old):
            raise ValueError("V45 changed inherited original code section length")
    def mapped(pc:int,n:int)->bytes:
        hits=[bytes(code[pc-base:pc-base+n]) for base,code in newtext
              if base<=pc and pc+n<=base+len(code)]
        if len(hits)!=1:
            raise ValueError("V45 guest PPC range missing or overlapping")
        return hits[0]
    raw=owner.read_bytes()
    if mapped(OLD_STOP,4)!=text_at(raw,OLD_STOP,4):
        raise ValueError("original OSInit interrupt BL modified")
    if mapped(AFTER_CALL,8)!=struct.pack(">II",SC,BLR):
        raise ValueError("V45 OSInit fallback service not test-bounded")
    if mapped(INTERRUPT,PREFIX_LENGTH)!=text_at(raw,INTERRUPT,PREFIX_LENGTH):
        raise ValueError("original __OSInterruptInit PPC modified")
    if mapped(STOP,8)!=struct.pack(">II",SC,BLR):
        raise ValueError("V45 MMIO/interrupt-mask next original code not bounded")
    if mapped(FILL,FILL_LENGTH)!=text_at(raw,FILL,FILL_LENGTH):
        raise ValueError("V45 original memset/__fill_mem PPC modified")

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_fixture",type=Path)
    p.add_argument("owner_original_dol",type=Path)
    a=p.parse_args()
    verify(a.private_fixture.read_bytes(),a.owner_original_dol)
    print("PASS: V45 original Wii IRQ, memset/fill instructions and no-overwrite guard")
