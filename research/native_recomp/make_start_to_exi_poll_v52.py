#!/usr/bin/env python3
"""V52 continuous owner-original __start -> OSInit -> EXIInit poll prefix.

All real PPC bytes are extracted from the SHA-pinned owner DOL. The DOL's
seven text slots are already occupied. Extend only the existing synthetic
DBPrintf text section across a guarded NOP gap, ending at a conspicuous
test-only sc;blr before __OSMaskInterrupts. No owner data is distributed.
"""
from __future__ import annotations
import argparse
import struct
from pathlib import Path

from make_start_to_cache_reuse_v51 import make as make_v51, STOP as OLD_STOP, START
from make_start_to_epilogue_v41 import sections_of
from make_start_to_module_v44 import locate
from make_osinit_execparams_v28 import text_at, SC, BLR, NOP
from make_alarm_v47 import call_target
from make_start_to_vectorcopy_v38 import word

OSINIT_CALL=0x805208C4
OSINIT_GUARD=0x805208C8
EXI=0x804EF9BC
STOP=0x804EFA14
DBINIT=0x804E5020
DEBUG=0x804E50B8
EXI_LENGTH=STOP-EXI

def verify_prefix(code:bytes)->None:
    if len(code)!=0x58 or word(code,0)!=0x9421FFE0:
        raise ValueError("original EXI prologue or length changed")
    for pc in (0x804EF9E8,0x804EF9F8,0x804EFA08):
        op=word(code,pc-EXI)
        if op>>26!=16:
            raise ValueError("original EXI branch opcode changed")
        disp=op&0xFFFC
        if disp&0x8000:disp-=0x10000
        if pc+disp!=0x804EF9DC:
            raise ValueError("original EXI busy-loop target changed")
    for pc in (0x804EF9DC,0x804EF9EC,0x804EF9FC):
        if word(code,pc-EXI)>>26!=32:
            raise ValueError("original EXI channel control register read changed")
    if word(code,0x804EFA10-EXI)>>26!=14:
        raise ValueError("original EXI mask argument calculation changed")

def make(owner:Path)->bytes:
    previous=make_v51(owner)  # all prior SHA, callgraph and guard checks
    raw=owner.read_bytes()
    if OLD_STOP!=OSINIT_CALL:
        raise ValueError("V51 checkpoint unexpectedly moved")
    call=text_at(raw,OSINIT_CALL,4)
    if call_target(call,OSINIT_CALL,OSINIT_CALL)!=EXI:
        raise ValueError("original Wii OSInit->EXIInit call target differs")
    prefix=text_at(raw,EXI,EXI_LENGTH)
    verify_prefix(prefix)
    os_at=locate(previous,OSINIT_CALL,12)
    if previous[os_at:os_at+12]!=struct.pack(">III",SC,BLR,NOP):
        raise ValueError("V51 OSInit test-only stop/padding overwritten")

    text,data=sections_of(previous)
    if len(text)!=7 or text[6][0]!=DBINIT:
        raise ValueError("V51 DBInit/DBPrintf text section address changed")
    base,code=text[6]
    if (len(code)!=DEBUG+8-base or
        code[DEBUG-base:DEBUG-base+8]!=struct.pack(">II",SC,BLR) or
        code[0:4]!=text_at(raw,DBINIT,4)):
        raise ValueError("V51 original DBInit or synthetic DBPrintf region changed")
    for guest,body in text[:6]:
        if guest<STOP+8 and guest+len(body)>base:
            raise ValueError("EXI text expansion overlaps independent text section")
    gap=EXI-(base+len(code))
    if gap<=0 or gap%4 or gap>0x20000:
        raise ValueError("EXI padding span out of bounds")
    code.extend(struct.pack(">I",NOP)*(gap//4))
    if len(code)!=EXI-base:
        raise ValueError("EXI guest address padding incorrectly calculated")
    code.extend(prefix)
    code.extend(struct.pack(">II",SC,BLR))
    if len(code)!=STOP+8-base:
        raise ValueError("EXI stop does not end final text section")
    text[6]=(base,code)

    result=bytearray(previous[:256])
    for i,(guest,body) in enumerate(text):
        at=len(result)
        for off,v in ((0,at),(0x48,guest),(0x90,len(body))):
            struct.pack_into(">I",result,off+4*i,v)
        result.extend(body)
        result.extend(b"\0"*((-len(result))%4))
    for i,(guest,body) in enumerate(data):
        at=len(result)
        for off,v in ((0x1C,at),(0x64,guest),(0xAC,len(body))):
            struct.pack_into(">I",result,off+4*i,v)
        result.extend(body)
        result.extend(b"\0"*((-len(result))%4))
    patch=locate(result,OSINIT_CALL,12)
    if result[patch:patch+12]!=struct.pack(">III",SC,BLR,NOP):
        raise ValueError("OSInit EXI insertion would overwrite non-synthetic code")
    # C4: authentic BL. C8: test-only sc. CC: test-only blr.
    result[patch:patch+12]=call+struct.pack(">II",SC,BLR)
    if word(result,0xE0)!=START:
        raise ValueError("original entry point unexpectedly changed")
    return bytes(result)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("owner_original_dol",type=Path)
    p.add_argument("private_fixture",type=Path)
    args=p.parse_args()
    if args.private_fixture.exists() or args.private_fixture.is_symlink():
        p.error("refusing to overwrite private owner fixture")
    args.private_fixture.write_bytes(make(args.owner_original_dol))
    print("PASS: original Wii V52 continuous EXI polling fixture generated privately")
