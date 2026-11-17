#!/usr/bin/env python3
"""V45 owner-private continuous __start -> original Wii interrupt-table prefix.

Only SHA-authenticated owner DOL supplies game PPC instructions. This private
AOT test runs original OSInit -> __OSInterruptInit -> memset -> __fill_mem,
stopping at 0x8052664C before unimplemented interrupt-mask/MMIO services.
No translated game code, proprietary binaries or logs enter the repository.
"""
from __future__ import annotations
import argparse
import struct
from pathlib import Path

from make_start_to_module_v44 import make as make_v44
from make_start_to_epilogue_v41 import sections_of
from make_start_to_vectorcopy_v38 import word
from make_osinit_execparams_v28 import text_at, SC, BLR, NOP
from make_interrupt_prefix_v50 import ENTRY as INTERRUPT, CALL as IRQ_CALL
from make_interrupt_prefix_v50 import STOP, MEMSET, FILL, target as original_bl

START=0x8000403C
OSINIT=0x80520670
OLD_STOP=0x805208B8
AFTER_CALL=OLD_STOP+4
FILL_LENGTH=0xE4
PREFIX_LENGTH=STOP-INTERRUPT
COPY=0x80004338

def make(owner:Path)->bytes:
    prior=make_v44(owner)  # nested SHA-pinned owner and previous original path
    raw=owner.read_bytes()
    text,data=sections_of(prior)
    os_matches=[i for i,(guest,code) in enumerate(text) if guest==OSINIT]
    if len(os_matches)!=1:
        raise ValueError("V45 existing OSInit section not uniquely mapped")
    os_index=os_matches[0]
    base,body=text[os_index]
    at=OLD_STOP-base
    if (body[at:at+8]!=struct.pack(">II",SC,BLR) or
        word(body,at+8)!=NOP):
        raise ValueError("V44 module-to-interrupt stop was modified")
    call=text_at(raw,OLD_STOP,4)
    if original_bl(word(call,0),OLD_STOP)!=INTERRUPT:
        raise ValueError("original Wii OSInit interrupt callsite changed")
    body[at:at+4]=call
    body[at+4:at+12]=struct.pack(">II",SC,BLR)
    text[os_index]=(base,body)

    irq=text_at(raw,INTERRUPT,PREFIX_LENGTH)
    fill=text_at(raw,FILL,FILL_LENGTH)
    if (len(irq)!=0x30 or len(fill)!=0xE4 or
        original_bl(word(irq,IRQ_CALL-INTERRUPT),IRQ_CALL)!=MEMSET or
        original_bl(word(fill,0x80004450-FILL),0x80004450)!=FILL):
        raise ValueError("original Wii interrupt/memset/fill BL graph changed")
    if (word(fill,0xB0)!=BLR or word(fill,0xE0)!=BLR or
        word(irq,0)!=0x9421FFE0):
        raise ValueError("original interrupt prologue/fill helper returns changed")

    irq_matches=[i for i,(guest,code) in enumerate(text)
                 if guest<=INTERRUPT and STOP+8<=guest+len(code)]
    if len(irq_matches)!=1:
        raise ValueError("V45 interrupt function not uniquely mapped")
    idx=irq_matches[0];base,code=text[idx]
    offset=INTERRUPT-base
    if code[offset:offset+PREFIX_LENGTH+8]!=struct.pack(">I",NOP)*((PREFIX_LENGTH+8)//4):
        raise ValueError("V45 interrupt code overlaps verified native instructions")
    code[offset:offset+PREFIX_LENGTH]=irq
    code[offset+PREFIX_LENGTH:offset+PREFIX_LENGTH+8]=struct.pack(">II",SC,BLR)
    text[idx]=(base,code)

    # __init_data already includes the authentic FILL/MEMSET instructions in
    # the contiguous original START text section. The owner-original V22
    # geometry and native V44 test previously verified both. Reuse them;
    # introducing another section would overlap original PPC guest addresses.
    matches=[(guest,code) for guest,code in text
             if guest<=FILL and FILL+FILL_LENGTH<=guest+len(code)]
    if len(matches)!=1:
        raise ValueError("V45 inherited memset/fill original text not mapped uniquely")
    guest,code=matches[0]
    at=FILL-guest
    if code[at:at+FILL_LENGTH]!=fill:
        raise ValueError("V45 inherited original memset/fill PPC differs")

    result=bytearray(prior[:256])
    for i,(guest,code) in enumerate(text):
        offset=len(result)
        for h,value in ((0,offset),(0x48,guest),(0x90,len(code))):
            struct.pack_into(">I",result,h+4*i,value)
        result.extend(code)
        result.extend(b"\0"*((-len(result))%4))
    for i,(guest,code) in enumerate(data):
        offset=len(result)
        for h,value in ((0x1c,offset),(0x64,guest),(0xac,len(code))):
            struct.pack_into(">I",result,h+4*i,value)
        result.extend(code)
        result.extend(b"\0"*((-len(result))%4))
    if word(result,0xE0)!=START:
        raise ValueError("V45 original Wii __start entry changed")
    return bytes(result)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("owner_original_dol",type=Path)
    p.add_argument("private_fixture",type=Path)
    a=p.parse_args()
    if a.private_fixture.exists() or a.private_fixture.is_symlink():
        p.error("refusing overwrite of owner-private V45 fixture")
    a.private_fixture.write_bytes(make(a.owner_original_dol))
    print("PASS: private continuous V45 original interrupt/memset/fill fixture generated")
