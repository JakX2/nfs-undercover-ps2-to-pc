#!/usr/bin/env python3
"""V54 continuous Wii original EXI interrupt handler registration.

V53 is reconstructed privately from SHA-256-pinned owner DOL; only the
previous synthetic test stop and a verified NOP handler region may change.
"""
from __future__ import annotations
import argparse
import struct
from pathlib import Path
from make_start_to_eximask_v53 import make as make_v53, STOP as OLD_STOP, EXI
from make_start_to_exi_poll_v52 import START
from make_start_to_epilogue_v41 import sections_of
from make_osinit_execparams_v28 import text_at, SC, BLR, NOP
from make_alarm_v47 import call_target
from make_start_to_vectorcopy_v38 import word

HANDLER=0x805265F8
HANDLER_SIZE=0x14
STOP=0x804EFAA0
CALL_SITES=(0x804EFA40,0x804EFA50,0x804EFA60,0x804EFA6C,
            0x804EFA78,0x804EFA84,0x804EFA90,0x804EFA9C)

def verify_original(raw:bytes)->tuple[bytes,bytes]:
    handler=text_at(raw,HANDLER,HANDLER_SIZE)
    exi=text_at(raw,EXI,STOP-EXI)
    if len(handler)!=HANDLER_SIZE or word(handler,0)>>26!=32 or word(handler,16)!=BLR:
        raise ValueError("original Wii interrupt handler setter changed")
    if (word(handler,4)>>26!=21 or
        word(handler,8)>>26!=31 or word(handler,12)>>26!=31):
        raise ValueError("original handler-table index/read/write opcodes changed")
    for pc in CALL_SITES:
        if call_target(exi,pc,EXI)!=HANDLER:
            raise ValueError("original EXI interrupt handler call target changed")
    return handler,exi

def make(owner:Path)->bytes:
    prev=make_v53(owner)
    handler,exi=verify_original(owner.read_bytes())
    text,data=sections_of(prev)
    if len(text)!=7 or len(data)!=2:
        raise ValueError("V53 inherited DOL layout changed")
    hits=[i for i,(base,code) in enumerate(text)
          if base<=HANDLER and HANDLER+HANDLER_SIZE<=base+len(code)]
    if len(hits)!=1:
        raise ValueError("original interrupt handler guest section unavailable")
    i=hits[0]
    base,code=text[i]
    at=HANDLER-base
    if code[at:at+HANDLER_SIZE]!=struct.pack(">I",NOP)*(HANDLER_SIZE//4):
        raise ValueError("interrupt handler body would overwrite existing PPC")
    code[at:at+HANDLER_SIZE]=handler
    text[i]=(base,code)
    base,exi_code=text[6]
    if (len(exi_code)!=OLD_STOP+8-base or
        exi_code[EXI-base:OLD_STOP-base]!=exi[:OLD_STOP-EXI] or
        exi_code[OLD_STOP-base:]!=struct.pack(">II",SC,BLR)):
        raise ValueError("V53 EXI mask prefix or test-only stop was modified")
    exi_code[OLD_STOP-base:]=exi[OLD_STOP-EXI:]+struct.pack(">II",SC,BLR)
    if len(exi_code)!=STOP+8-base:
        raise ValueError("V54 EXI synthetic stop not aligned")
    text[6]=(base,exi_code)
    out=bytearray(prev[:256])
    for i,(base,blob) in enumerate(text):
        at=len(out)
        for h,v in ((0,at),(0x48,base),(0x90,len(blob))):
            struct.pack_into(">I",out,h+4*i,v)
        out.extend(blob)
        out.extend(b"\0"*((-len(out))%4))
    for i,(base,blob) in enumerate(data):
        at=len(out)
        for h,v in ((0x1C,at),(0x64,base),(0xAC,len(blob))):
            struct.pack_into(">I",out,h+4*i,v)
        out.extend(blob)
        out.extend(b"\0"*((-len(out))%4))
    if word(out,0xE0)!=START:
        raise ValueError("original Wii __start entry changed")
    return bytes(out)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("owner_dol",type=Path)
    p.add_argument("private_output",type=Path)
    a=p.parse_args()
    if a.private_output.exists() or a.private_output.is_symlink():
        p.error("refusing overwrite of owner-private fixture")
    a.private_output.write_bytes(make(a.owner_dol))
    print("PASS: original Wii V54 eight EXI interrupt-handler registrations fixture")
