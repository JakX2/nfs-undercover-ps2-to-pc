#!/usr/bin/env python3
"""V47 owner-private continuous original Wii IRQ disable/mask-state AOT slice.

Extends the verified V46 native __start path inside __OSInterruptInit.
All genuine PowerPC words are extracted exclusively from the SHA-pinned
original owner DOL; no owner instructions or binary data are committed.
"""
from __future__ import annotations
import argparse
import struct
from pathlib import Path
from make_start_to_interrupt_mmio_v46 import make as make_v46, NEW_STOP as OLD_STOP
from make_start_to_module_v44 import locate
from make_start_to_vectorcopy_v38 import word
from make_osinit_execparams_v28 import text_at,SC,BLR,NOP
from make_alarm_v47 import call_target

STOP=0x80526698
DISABLE=0x805265AC
START=0x8000403C

def is_stw(ins:int,reg:int,base:int,disp:int)->bool:
    return (ins>>26==36 and ((ins>>21)&31)==reg and
            ((ins>>16)&31)==base and (ins&0xffff)==disp)

def make(owner:Path)->bytes:
    previous=make_v46(owner)  # transitive exact original DOL fingerprint
    code=text_at(owner.read_bytes(),OLD_STOP,STOP-OLD_STOP)
    if (len(code)!=0x24 or
        call_target(code,OLD_STOP,OLD_STOP)!=DISABLE or
        not is_stw(word(code,0x18),30,31,0xC4)):
        raise ValueError("V47 genuine Wii interrupt disable/mask-store call graph changed")
    offset=locate(previous,OLD_STOP,len(code)+8)
    if previous[offset:offset+8]!=struct.pack(">II",SC,BLR):
        raise ValueError("V46 private interrupt/MMIO boundary was modified")
    if previous[offset+8:offset+len(code)+8]!=struct.pack(">I",NOP)*(len(code)//4):
        raise ValueError("V47 would overwrite prior native code")
    out=bytearray(previous)
    out[offset:offset+len(code)]=code
    out[offset+len(code):offset+len(code)+8]=struct.pack(">II",SC,BLR)
    if out[:256]!=previous[:256] or word(out,0xE0)!=START:
        raise ValueError("V47 unexpectedly changed guest Wii DOL header or entry")
    return bytes(out)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("owner_original_dol",type=Path)
    p.add_argument("private_fixture",type=Path)
    args=p.parse_args()
    if args.private_fixture.exists() or args.private_fixture.is_symlink():
        p.error("refusing overwrite of SHA-authenticated private DOL")
    args.private_fixture.write_bytes(make(args.owner_original_dol))
    print("PASS: V47 owner-private continuous original IRQ disable/mask fixture generated")
