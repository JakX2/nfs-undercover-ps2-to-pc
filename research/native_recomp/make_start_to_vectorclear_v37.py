#!/usr/bin/env python3
"""Owner-private V37 Wii __start through authentic exception-template clear loop.

All original PowerPC words are extracted exclusively from the exact owner DOL
in temporary scratch. This code contains only original-free constructor logic.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import hashlib
import struct

from make_start_to_mark_v36 import make as make_v36, OSINIT, STOP as OLD_STOP, MARK_FIRST, word
from make_osinit_vectorclear_v41 import (
    FIRST_ORIGINAL, ORIGINAL_END, FIRST_DEBUG, SECOND_DEBUG, VECTOR_COPY_STOP
)
from make_hardware_boundary_v17 import ORIGINAL_SHA,get_text
from make_start_to_data_v23 import SC,BLR

STOP = VECTOR_COPY_STOP


def make(owner:Path)->bytes:
    original=owner.read_bytes()
    if hashlib.sha256(original).hexdigest()!=ORIGINAL_SHA:
        raise ValueError("original owner Wii executable SHA-256 mismatch")
    prev=make_v36(owner)
    sections=[]
    for i in range(7):
        off,guest,count=(word(prev,k+4*i) for k in (0,0x48,0x90))
        if off<256 or count<4 or off+count>len(prev):
            raise ValueError("invalid inherited original V36 section")
        sections.append((guest,bytearray(prev[off:off+count])))
    if sections[1][0]!=OSINIT:
        raise ValueError("Wii OSInit address moved unexpectedly")
    guest,os=sections[1]
    for pc in (MARK_FIRST,OLD_STOP):
        if os[pc-guest:pc-guest+8]!=struct.pack(">II",SC,BLR):
            raise ValueError("previous original exception mark stop was modified")
    original_body=get_text(original,FIRST_ORIGINAL,ORIGINAL_END-FIRST_ORIGINAL)
    if len(original_body)!=0xB8:
        raise ValueError("original Wii exception-template loop truncated")
    for pc,op in ((0x80520CC8,0x2C030000),
                  (0x80520CCC,0x41820018),
                  (0x80520CF4,0x2C030000),
                  (0x80520CF8,0x41820028),
                  (0x80520D20,0x28150000),
                  (0x80520D64,0x4200FFDC),
                  (0x80520D7C,0x4200FFF8)):
        if word(original_body,pc-FIRST_ORIGINAL)!=op:
            raise ValueError("original Wii exception-template PPC branch changed")
    for pc in (FIRST_DEBUG,SECOND_DEBUG):
        if word(original_body,pc-FIRST_ORIGINAL)>>26 != 18:
            raise ValueError("original Wii debug callback callsite changed")

    at=FIRST_ORIGINAL-guest
    if at<0 or STOP+8>guest+len(os):
        raise ValueError("exception clearing loop exceeds private Wii segment")
    os[at:STOP-guest]=original_body
    for pc in (FIRST_DEBUG,SECOND_DEBUG,STOP):
        struct.pack_into(">I",os,pc-guest,SC)
        if pc==STOP:
            struct.pack_into(">I",os,pc+4-guest,BLR)
    sections[1]=(guest,os)

    data_off,data_count=word(prev,0x1c),word(prev,0xac)
    if data_off<256 or data_count!=0xb0 or data_off+data_count>len(prev):
        raise ValueError("original Wii BSS table changed")
    data=prev[data_off:data_off+data_count]
    image=bytearray(256+sum((len(part)+3)&~3 for _,part in sections)+len(data))
    cursor=256
    for i,(base,part) in enumerate(sections):
        for k,v in ((0,cursor),(0x48,base),(0x90,len(part))):
            struct.pack_into(">I",image,k+4*i,v)
        image[cursor:cursor+len(part)]=part
        cursor+=(len(part)+3)&~3
    for k,v in ((0x1c,cursor),(0x64,0x80006420),(0xac,len(data))):
        struct.pack_into(">I",image,k,v)
    image[cursor:cursor+len(data)]=data
    struct.pack_into(">I",image,0xe0,0x8000403C)
    return bytes(image)


if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("owner_original_dol",type=Path)
    cli.add_argument("private_test_dol",type=Path)
    args=cli.parse_args()
    if args.private_test_dol.exists() or args.private_test_dol.is_symlink():
        cli.error("refusing overwrite of owner-private Wii DOL")
    args.private_test_dol.write_bytes(make(args.owner_original_dol))
    print("PASS: private original Wii V37 continuous exception template loop fixture")
