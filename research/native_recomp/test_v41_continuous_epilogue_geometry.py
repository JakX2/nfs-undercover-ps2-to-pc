#!/usr/bin/env python3
"""V41 fail-closed original exception epilogue, restore and mapping verification."""
from __future__ import annotations
import argparse
from pathlib import Path
import struct
from make_start_to_vectors_v40 import make as make_v40
from make_start_to_epilogue_v41 import sections_of,STOP,START
from make_start_to_vectorcopy_v38 import word
from make_osinit_execparams_v28 import text_at,SC,BLR
from make_osinit_syscall_bridge_v46 import (
    EXCEPTION_RETURN_START, EXCEPTION_RETURN_END, RESTORE, RESTORE_END
)

def extract(text:list,pc:int,n:int)->bytes:
    matches=[bytes(code[pc-guest:pc-guest+n]) for guest,code in text
             if guest<=pc and pc+n<=guest+len(code)]
    if len(matches)!=1:
        raise ValueError("V41 original Wii instruction range has ambiguous mapping")
    return matches[0]

def verify(actual:bytes,owner:Path)->None:
    original=owner.read_bytes()
    prior=make_v40(owner)  # SHA and all V40 original code guards
    if word(actual,0xE0)!=START or actual[:0xE0]!=prior[:0xE0]:
        # DOL offsets and sizes may legitimately differ; check them below.
        if word(actual,0xE0)!=START:
            raise ValueError("V41 Wii entry point changed")
    old_text,old_data=sections_of(prior)
    new_text,new_data=sections_of(actual)
    if [g for g,_ in old_text]!=[g for g,_ in new_text]:
        raise ValueError("V41 original PPC text bases reordered")
    if [(g,bytes(b)) for g,b in old_data]!=[(g,bytes(b)) for g,b in new_data]:
        raise ValueError("V41 private startup table or oracle changed")
    allowed=((EXCEPTION_RETURN_START,EXCEPTION_RETURN_END),
             (RESTORE,RESTORE_END))
    for (guest,old),(other,now) in zip(old_text,new_text):
        if guest!=other or len(now)<len(old):
            raise ValueError("V41 original text base/size regressed")
        for index in range(len(old)):
            pc=guest+index
            if not any(lo<=pc<hi for lo,hi in allowed) and old[index]!=now[index]:
                raise ValueError("V41 modified previously verified PPC instruction")
        if len(now)>len(old):
            for index in range(len(old),len(now)):
                pc=guest+index
                if RESTORE<=pc<RESTORE_END:
                    continue
                if not (0x805450E8<=pc<RESTORE):
                    raise ValueError("V41 appended bytes outside restore thunk gap")
                if now[index]!=struct.pack(">I",0x60000000)[(pc-guest)%4]:
                    raise ValueError("V41 restore thunk gap not padded with PPC NOPs")
    for first,last in allowed:
        if extract(new_text,first,last-first)!=text_at(original,first,last-first):
            raise ValueError("V41 original PPC exception tail/restore mismatch")
    if extract(new_text,STOP,8)!=struct.pack(">II",SC,BLR):
        raise ValueError("V41 OSInit return stop no longer guarded")
    if extract(new_text,0x804E50B8,8)!=struct.pack(">II",SC,BLR):
        raise ValueError("V41 DBPrintf remains unresolved and must be bounded")

if __name__=="__main__":
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("private_fixture",type=Path)
    ap.add_argument("owner_original_dol",type=Path)
    a=ap.parse_args()
    verify(a.private_fixture.read_bytes(),a.owner_original_dol)
    print("PASS: V41 original exception-return/restore PPC and inherited privacy guards")
