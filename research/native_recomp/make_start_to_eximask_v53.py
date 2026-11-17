#!/usr/bin/env python3
"""V53 continuous Wii __start -> OSInit -> original EXIInit mask/MMIO.

Only owner SHA-pinned DOL supplies PowerPC opcodes; synthetic sc;blr marks
the first unimplemented EXI handler-install callsite at 0x804EFA34.
"""
from __future__ import annotations
import argparse
import struct
from pathlib import Path
from make_start_to_exi_poll_v52 import make as make_v52, STOP as OLD_STOP, EXI, START, DBINIT
from make_start_to_epilogue_v41 import sections_of
from make_osinit_execparams_v28 import text_at, SC, BLR, NOP
from make_alarm_v47 import call_target
from make_start_to_vectorcopy_v38 import word

MASK=0x8052693C
MASK_SIZE=0x80
EXI_MASK_CALL=OLD_STOP
STOP=0x804EFA34

def verify_original(raw:bytes)->tuple[bytes,bytes]:
    mask=text_at(raw,MASK,MASK_SIZE)
    exi=text_at(raw,EXI,STOP-EXI)
    if len(mask)!=MASK_SIZE or word(mask,0)>>26!=37 or word(mask,MASK_SIZE-4)!=BLR:
        raise ValueError("original Wii mask prologue or return changed")
    if call_target(exi,EXI_MASK_CALL,EXI)!=MASK:
        raise ValueError("original EXIInit mask branch destination changed")
    for pc,dest in ((0x80526958,0x805265AC),
                    (0x80526988,0x805266E0),
                    (0x80526998,0x805265D4)):
        if call_target(mask,pc,MASK)!=dest:
            raise ValueError("original mask function nested BL graph changed")
    for pc in (0x804EFA20,0x804EFA24,0x804EFA28,0x804EFA30):
        if word(exi,pc-EXI)>>26!=36:
            raise ValueError("original EXI MMIO write opcode changed")
    return mask,exi

def make(owner:Path)->bytes:
    prev=make_v52(owner)
    mask,exi=verify_original(owner.read_bytes())
    text,data=sections_of(prev)
    if len(text)!=7 or len(data)!=2 or text[6][0]!=DBINIT:
        raise ValueError("V52 seven-text/two-data DOL geometry changed")
    matches=[i for i,(base,code) in enumerate(text)
             if base<=MASK and MASK+MASK_SIZE<=base+len(code)]
    if len(matches)!=1:
        raise ValueError("original mask guest range not uniquely mapped")
    at_index=matches[0]
    base,code=text[at_index]
    at=MASK-base
    if code[at:at+MASK_SIZE]!=struct.pack(">I",NOP)*(MASK_SIZE//4):
        raise ValueError("refuse overwrite of translated Wii PPC at mask destination")
    code[at:at+MASK_SIZE]=mask
    text[at_index]=(base,code)
    base,exi_code=text[6]
    if (len(exi_code)!=OLD_STOP+8-base or
        exi_code[EXI-base:OLD_STOP-base]!=exi[:OLD_STOP-EXI] or
        exi_code[OLD_STOP-base:]!=struct.pack(">II",SC,BLR)):
        raise ValueError("V52 original EXI prefix or synthetic terminal altered")
    exi_code[OLD_STOP-base:]=exi[OLD_STOP-EXI:]+struct.pack(">II",SC,BLR)
    if len(exi_code)!=STOP+8-base:
        raise ValueError("V53 EXI terminal not at exact next service")
    text[6]=(base,exi_code)
    out=bytearray(prev[:256])
    for i,(base,blob) in enumerate(text):
        at=len(out)
        for header,value in ((0,at),(0x48,base),(0x90,len(blob))):
            struct.pack_into(">I",out,header+4*i,value)
        out.extend(blob)
        out.extend(b"\0"*((-len(out))%4))
    for i,(base,blob) in enumerate(data):
        at=len(out)
        for header,value in ((0x1C,at),(0x64,base),(0xAC,len(blob))):
            struct.pack_into(">I",out,header+4*i,value)
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
    print("PASS: V53 original EXI mask + MMIO private fixture generated")
