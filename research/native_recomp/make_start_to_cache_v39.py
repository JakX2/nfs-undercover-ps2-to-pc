#!/usr/bin/env python3
"""Construct owner-private V39 continuous __start cache-loop test DOL.

The original PowerPC instructions come exclusively from the SHA-pinned owner
Wii game executable; this file contains no copied proprietary instructions.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import struct
from make_start_to_vectorcopy_v38 import make as make_v38, STOP as PREVIOUS_STOP, OSINIT, word
from make_osinit_cache_v43 import FIRST_CACHE,FIRST_CACHE_LEN,SECOND_CACHE,SECOND_CACHE_LEN,END_STOP
from make_osinit_execparams_v28 import text_at,target,SC,BLR

STOP=END_STOP

def make(owner:Path)->bytes:
    image=bytearray(make_v38(owner))
    if PREVIOUS_STOP!=0x80520DA4 or STOP!=0x80520DB8:
        raise ValueError("previous continuous Wii startup stage changed")
    raw=owner.read_bytes() # SHA-pinned by make_v38
    first=text_at(raw,FIRST_CACHE,FIRST_CACHE_LEN)
    second=text_at(raw,SECOND_CACHE,SECOND_CACHE_LEN)
    continuation=text_at(raw,PREVIOUS_STOP,STOP-PREVIOUS_STOP)
    if len(first)!=0x2C or len(second)!=0x34 or len(continuation)!=0x14:
        raise ValueError("owner-original Wii cache code incomplete")
    if target(word(continuation,0),PREVIOUS_STOP,True)!=FIRST_CACHE:
        raise ValueError("original DCFlushRangeNoSync call differs")
    if target(word(continuation,0x10),STOP-4,True)!=SECOND_CACHE:
        raise ValueError("original ICInvalidateRange call differs")
    if word(first,FIRST_CACHE_LEN-4)!=BLR or word(second,SECOND_CACHE_LEN-4)!=BLR:
        raise ValueError("original Wii cache helper return missing")
    if word(first,0x1C)>>26!=31 or word(second,0x1C)>>26!=31:
        raise ValueError("original cache-line instruction changed")
    off,guest,count=(word(image,k) for k in (0,0x48,0x90))
    if off<256 or guest!=OSINIT or STOP+8>guest+count:
        raise ValueError("continuous startup section lacks bounded cache continuation")
    start=off+PREVIOUS_STOP-guest
    if image[start:start+8]!=struct.pack(">II",SC,BLR):
        raise ValueError("V38 test-only stop no longer matches")
    # Continuous startup uses seven disjoint text sections. Cache services
    # live in the original DCEnable/ICEnable region (section 3), not the OSInit
    # section (section 1) used by the older direct-entry V43 fixture.
    cache_off,cache_guest,cache_count=(word(image,k+4*3) for k in (0,0x48,0x90))
    if cache_off<256 or cache_guest!=0x80522280 or cache_off+cache_count>len(image):
        raise ValueError("original Wii cache-control text section changed")
    for base,code in ((FIRST_CACHE,first),(SECOND_CACHE,second)):
        at=cache_off+base-cache_guest
        if at<cache_off or at+len(code)>cache_off+cache_count:
            raise ValueError("owner cache helper not contained in cache-control section")
        for index in range(0,len(code),4):
            if word(image,at+index)!=0x60000000:
                raise ValueError("cache helper overlaps previously translated native code")
        image[at:at+len(code)]=code
    image[start:start+len(continuation)]=continuation
    at=off+STOP-guest
    if image[at:at+8]!=struct.pack(">II",0x60000000,0x60000000):
        raise ValueError("new bounded stop overlaps previously translated PPC")
    struct.pack_into(">II",image,at,SC,BLR)
    return bytes(image)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("owner_original_dol",type=Path)
    p.add_argument("private_destination",type=Path)
    a=p.parse_args()
    if a.private_destination.exists() or a.private_destination.is_symlink():
        p.error("refusing to overwrite owner-private test image")
    a.private_destination.write_bytes(make(a.owner_original_dol))
    print("PASS: V39 owner-original continuous startup cache-loop test fixture built privately")
