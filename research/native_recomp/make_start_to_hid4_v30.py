#!/usr/bin/env python3
"""Private V30 continuous __start fixture: original HID4/speculation/FPSCR.

Original machine code comes ONLY from the SHA-pinned owner DOL in RAM and
private temporary files. Keep all generated output out of public Git.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import struct

from make_start_to_perfsprs_v29 import make as make_v29
from make_start_to_execparams_v28 import section_offset
from make_hardware_boundary_v17 import ORIGINAL_SHA, get_text, linked_target
from make_start_to_data_v23 import SC, BLR, NOP

OSINIT=0x80520670
PREVIOUS=0x805206F0
STOP=0x80520700
REPORT=0x80522F00
CACHE=0x80522540
HELPERS=0x804B7910
HID0_READ=0x804B7920
HID0_WRITE=0x804B7928
PERF=0x804B7964
SPEC=0x804B7A00
NONIEEE=0x804B7A28
HID4=0x804B7A30
HID_END=HID4+80

def be32(b:bytes,pos:int)->int:
    return struct.unpack_from(">I",b,pos)[0]

def spr_number(op:int)->int:
    return (((op>>11)&31)<<5)|((op>>16)&31)

def make(owner:Path)->bytes:
    raw=owner.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=ORIGINAL_SHA:
        raise ValueError("owner-original Wii DOL SHA-256 mismatch")
    v29=make_v29(owner)
    sections=[]
    for i in range(7):
        off,addr,length=(be32(v29,base+4*i) for base in (0,0x48,0x90))
        if off<256 or not length or off+length>len(v29):
            raise ValueError("invalid original V29 DOL section geometry")
        sections.append((addr,bytearray(v29[off:off+length])))
    if sections[1][0]!=OSINIT or sections[2][0]!=HELPERS or sections[5][0]!=CACHE:
        raise ValueError("unexpected inherited original guest section positions")

    os=sections[1][1]
    at=PREVIOUS-OSINIT
    if os[at:at+8]!=struct.pack(">II",SC,BLR):
        raise ValueError("previous V29 exact callback stop missing")
    continuation=get_text(raw,PREVIOUS,STOP-PREVIOUS)
    for pc,dest in ((0x805206F4,HID4),(0x805206F8,SPEC),
                    (0x805206FC,NONIEEE)):
        if linked_target(be32(continuation,pc-PREVIOUS),pc)!=dest:
            raise ValueError("original HID4/speculation/FP call graph changed")
    os[at:at+len(continuation)]=continuation
    os[STOP-OSINIT:STOP-OSINIT+8]=struct.pack(">II",SC,BLR)
    sections[1]=(OSINIT,os)

    helpers=sections[2][1]
    required=HID_END-HELPERS
    if not len(helpers)<required<200000 or required&3:
        raise ValueError("unexpected Wii HID4 code helper geometry")
    helpers.extend(NOP.to_bytes(4,"big")*((required-len(helpers))//4))
    original_hid0_read=get_text(raw,HID0_READ,8)
    if helpers[HID0_READ-HELPERS:HID0_READ-HELPERS+8]!=original_hid0_read:
        raise ValueError("V29 original PPC HID0 read helper changed")
    wrappers=((HID0_WRITE,8),(SPEC,40),(NONIEEE,8),(HID4,80))
    for pc,length in wrappers:
        body=get_text(raw,pc,length)
        if be32(body,length-4)!=BLR:
            raise ValueError("original hardware helper lacks complete return")
        helpers[pc-HELPERS:pc-HELPERS+length]=body
    # Preserve all six genuine performance helpers from the verified V29.
    for pc in range(PERF,PERF+48,8):
        if helpers[pc-HELPERS:pc-HELPERS+8]!=get_text(raw,pc,8):
            raise ValueError("original performance helper changed during V30 extension")
    hid4=helpers[HID4-HELPERS:HID4-HELPERS+80]
    if (spr_number(be32(hid4,0x1c))!=1011 or
        spr_number(be32(hid4,0x38))!=1011 or
        linked_target(be32(hid4,0x30),HID4+0x30)!=REPORT):
        raise ValueError("original HID4 code or guarded report branch changed")
    spec=helpers[SPEC-HELPERS:SPEC-HELPERS+40]
    if (linked_target(be32(spec,0x0c),SPEC+0x0c)!=HID0_READ or
        linked_target(be32(spec,0x14),SPEC+0x14)!=HID0_WRITE):
        raise ValueError("original speculative HID0 helper calls changed")
    if (spr_number(be32(helpers,HID0_WRITE-HELPERS))!=1008 or
        (be32(helpers,HID0_WRITE-HELPERS)>>1)&1023!=467):
        raise ValueError("original HID0 write SPR encoding changed")
    fp=be32(helpers,NONIEEE-HELPERS)
    if fp>>26!=63 or (fp>>1)&1023!=38 or (fp>>21)&31!=29:
        raise ValueError("original FP non-IEEE mtfsb1 encoding changed")
    sections[2]=(HELPERS,helpers)

    cache=sections[5][1]
    at=REPORT-CACHE
    if cache[at:at+8]!=NOP.to_bytes(4,"big")*2:
        raise ValueError("V30 original OSReport must be a test-only stop")
    cache[at:at+8]=struct.pack(">II",SC,BLR)
    sections[5]=(CACHE,cache)

    data_off,data_len=be32(v29,0x1c),be32(v29,0xac)
    if data_len!=0xb0 or data_off<256 or data_off+data_len>len(v29):
        raise ValueError("original startup BSS relocation table unavailable")
    data=v29[data_off:data_off+data_len]
    out=bytearray(256+sum((len(part)+3)&~3 for _,part in sections)+len(data))
    pos=256
    for i,(guest,payload) in enumerate(sections):
        for field,value in ((0,pos),(0x48,guest),(0x90,len(payload))):
            struct.pack_into(">I",out,field+i*4,value)
        out[pos:pos+len(payload)]=payload
        pos+=(len(payload)+3)&~3
    for field,value in ((0x1c,pos),(0x64,0x80006420),(0xac,len(data))):
        struct.pack_into(">I",out,field,value)
    out[pos:pos+len(data)]=data
    struct.pack_into(">I",out,0xe0,0x8000403C)
    return bytes(out)

def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("original_dol",type=Path)
    p.add_argument("private_output_dol",type=Path)
    args=p.parse_args()
    if args.private_output_dol.exists() or args.private_output_dol.is_symlink():
        p.error("refusing owner-private output overwrite")
    args.private_output_dol.write_bytes(make(args.original_dol))
    print("PASS: original V30 continuous startup HID4/speculation/FP fixture generated privately")

if __name__=="__main__":
    main()
