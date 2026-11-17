#!/usr/bin/env python3
"""Owner-private V44 continuous Wii __start -> original __OSModuleInit.

Reads authentic PowerPC exclusively from the SHA-pinned game owner's DOL;
the preceding V43 alarm/shutdown and V42 system-call native tests are
retained. The next Wii OSInit service is deliberately stopped with sc;blr.
"""
from __future__ import annotations
import argparse
import struct
from pathlib import Path
from make_start_to_alarm_v43 import make as make_v43
from make_start_to_vectorcopy_v38 import word
from make_osinit_execparams_v28 import SC,BLR,NOP
from make_alarm_v47 import original_text,call_target

MODULE=0x80526D30
OLD_STOP=0x805208B4
STOP=0x805208B8
START=0x8000403C

def locate(image:bytes,pc:int,size:int)->int:
    offsets=[]
    for i in range(7):
        off,base,length=(word(image,k+4*i) for k in (0,0x48,0x90))
        if base<=pc and pc+size<=base+length:
            if off<256 or off+length>len(image):
                raise ValueError("V44 original section outside owner-private DOL")
            offsets.append(off+pc-base)
    if len(offsets)!=1:
        raise ValueError("V44 target instruction range not mapped uniquely")
    return offsets[0]

def make(owner:Path)->bytes:
    prior=make_v43(owner)
    raw=owner.read_bytes()
    result=bytearray(prior)
    at=locate(prior,OLD_STOP,12)
    if prior[at:at+8]!=struct.pack(">II",SC,BLR) or word(prior,at+8)!=NOP:
        raise ValueError("V43 alarm-to-module test boundary modified")
    call=original_text(raw,OLD_STOP,4)
    module=original_text(raw,MODULE,24)
    if call_target(call,OLD_STOP,OLD_STOP)!=MODULE:
        raise ValueError("original Wii __OSModuleInit call target differs")
    if len(module)!=24 or word(module,20)!=BLR:
        raise ValueError("genuine Wii OSModuleInit return/body incomplete")
    module_at=locate(prior,MODULE,len(module))
    if prior[module_at:module_at+len(module)]!=struct.pack(">I",NOP)*6:
        raise ValueError("V44 genuine module helper overlaps earlier PPC translation")
    result[at:at+4]=call
    result[at+4:at+12]=struct.pack(">II",SC,BLR)
    result[module_at:module_at+len(module)]=module
    if word(result,0xE0)!=START or result[:256]!=prior[:256]:
        raise ValueError("V44 unexpectedly modified original Wii DOL metadata")
    return bytes(result)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("owner_original_dol",type=Path)
    p.add_argument("private_fixture",type=Path)
    a=p.parse_args()
    if a.private_fixture.exists() or a.private_fixture.is_symlink():
        p.error("refusing to overwrite owner-private original code fixture")
    a.private_fixture.write_bytes(make(a.owner_original_dol))
    print("PASS: owner-private original Wii V44 module initialization fixture")
