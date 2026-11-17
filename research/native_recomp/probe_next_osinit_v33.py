#!/usr/bin/env python3
"""Privacy-bounded Wii OSInit future-call scanner.

This performs STATIC METADATA ANALYSIS ONLY, not native instruction execution.
It reads a locally SHA-256-pinned owner DOL and emits only a small allowlisted
list of guest callsite/target addresses and instruction-class counts. No raw
opcodes, disassembly, game executable, symbol names, original C++ translation
or full function inventories are printed or committed.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
from pathlib import Path
import struct

from make_hardware_boundary_v17 import ORIGINAL_SHA,get_text

START=0x80520818
LENGTH=0x200
MAX_CALLS=12


def branch_target(op:int,pc:int)->int:
    if (op>>26)!=18:
        raise ValueError("not a direct PPC branch")
    disp=op&0x03FFFFFC
    if disp&0x02000000:
        disp-=0x04000000
    return (disp if op&2 else pc+disp)&0xFFFFFFFF


def classify(code:bytes,start:int=START)->tuple[Counter,list[tuple[int,int]]]:
    if len(code)==0 or len(code)&3 or len(code)>4096:
        raise ValueError("unbounded/unaligned private PowerPC span")
    counts=Counter()
    calls=[]
    for index in range(0,len(code),4):
        op=struct.unpack_from(">I",code,index)[0]
        pc=start+index
        major=op>>26
        if major==18:
            if op&1:
                counts["direct_calls"]+=1
                calls.append((pc,branch_target(op,pc)))
            else:
                counts["direct_branches"]+=1
        elif major==16:
            counts["conditional_branches"]+=1
        elif major in (32,33,34,35,40,41,42,43,46,47):
            counts["loads"]+=1
        elif major in (36,37,38,39,44,45,48,49,50,51,52,53,54,55):
            counts["stores_or_fp_memory"]+=1
        elif major==17:
            counts["syscalls"]+=1
        elif major==31:
            counts["extended_integer_or_spr"]+=1
        else:
            counts["other"]+=1
    if sum(counts.values())!=len(code)//4:
        raise ValueError("PPC instruction class count mismatch")
    return counts,calls


def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("owner_dol",type=Path)
    args=p.parse_args()
    raw=args.owner_dol.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=ORIGINAL_SHA:
        raise ValueError("wrong owner original Wii executable SHA-256")
    counts,calls=classify(get_text(raw,START,LENGTH),START)
    print(f"PASS: private original Wii next-OSInit static scan span=0x{START:08X}+0x{LENGTH:X} instructions={LENGTH//4}")
    for label in ("direct_calls","conditional_branches","direct_branches",
                  "loads","stores_or_fp_memory","syscalls","extended_integer_or_spr","other"):
        print(f"OSINIT_NEXT_CLASS {label}={counts[label]}")
    print(f"OSINIT_NEXT_DIRECT_CALLS count={len(calls)} shown={min(MAX_CALLS,len(calls))}")
    for site,target in calls[:MAX_CALLS]:
        # Guest code addresses only. No original PowerPC instruction words.
        print(f"OSINIT_NEXT_CALL site=0x{site:08X} guest_target=0x{target:08X}")


if __name__=="__main__":
    main()
