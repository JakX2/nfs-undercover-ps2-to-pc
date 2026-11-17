#!/usr/bin/env python3
"""Validate exact original six MMCR/PMC native test-call slices privately."""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import struct

from make_start_to_perfsprs_v29 import OSINIT,PREV_STOP,NEW_STOP,PERF,PERF_REGS,spr_num
from make_start_to_execparams_v28 import section_offset
from make_hardware_boundary_v17 import ORIGINAL_SHA,get_text,linked_target
from make_start_to_data_v23 import SC,BLR


def verify(image: bytes, source: bytes) -> None:
    if hashlib.sha256(source).hexdigest()!=ORIGINAL_SHA:
        raise ValueError("owner original Wii DOL does not match SHA pin")
    if len(image)<256 or struct.unpack_from(">I",image,0xe0)[0]!=0x8000403C:
        raise ValueError("authentic continuous startup entry missing")
    os_at=section_offset(image,1,PREV_STOP,NEW_STOP-PREV_STOP+8)
    if image[os_at:os_at+48]!=get_text(source,PREV_STOP,48):
        raise ValueError("authentic six original performance callsites changed")
    if image[os_at+48:os_at+56]!=struct.pack(">II",SC,BLR):
        raise ValueError("expected bounded 0x805206F0 synthetic stop")
    for i,spr in enumerate(PERF_REGS):
        pc=PERF+i*8
        at=section_offset(image,2,pc,8)
        extracted=image[at:at+8]
        if extracted!=get_text(source,pc,8):
            raise ValueError("original performance-helper body differs")
        opcode,tail=struct.unpack(">II",extracted)
        if (opcode>>26!=31 or (opcode>>1)&1023!=467 or
            spr_num(opcode)!=spr or tail!=BLR):
            raise ValueError("unexpected PPC MMCR/PMC helper encoding")
        callpc=PREV_STOP+4+8*i
        branch=struct.unpack_from(">I",image,os_at+4+8*i)[0]
        if linked_target(branch,callpc)!=pc:
            raise ValueError("original OSInit performance call topology changed")
    # No reserved Wii DOL code slots may overlap in the guest address space.
    ranges=[]
    for i in range(7):
        off,pc,size=(struct.unpack_from(">I",image,base+4*i)[0]
                      for base in (0,0x48,0x90))
        if off<256 or not size or off+size>len(image):
            raise ValueError("invalid private text layout")
        for start,end in ranges:
            if not(pc>=end or pc+size<=start):
                raise ValueError("overlapping guest PPC code slots")
        ranges.append((pc,pc+size))


def main()->None:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("private_dol",type=Path)
    ap.add_argument("original_dol",type=Path)
    args=ap.parse_args()
    verify(args.private_dol.read_bytes(),args.original_dol.read_bytes())
    print("PASS: original V29 six performance MMCR/PMC call and stop geometry")


if __name__=="__main__":
    main()
