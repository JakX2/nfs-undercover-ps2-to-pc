#!/usr/bin/env python3
"""Owner-local bounded OSInit tail / chronological startup frontier metadata."""
import argparse
import hashlib
import struct
from pathlib import Path
from make_hardware_boundary_v17 import ORIGINAL_SHA,get_text
from make_private_elf_symbol_map import ORIGINAL_SHA256,parse_functions
from probe_next_osinit_v33 import classify,branch_target
from probe_post_v68 import describe,MAX_SIZE

OSINIT=0x80520670
ENTRY=0x8000403c
OS_TAIL=0x80520968
START_TAIL=0x80004160
MAX_TAIL=0x400
MAX_NODES=24
ROOTS=(0x8052f790,0x8052f830,0x8052be14,0x8051e7e4,0x8052f94c,0x8051dff4)

def tail(raw,funcs,entry,start):
    end=entry+funcs.get(entry,0)
    if not start<end or end-start>MAX_TAIL or (end-start)%4:
        raise ValueError("V90 original startup tail outside bounded function")
    code=get_text(raw,start,end-start)
    _,calls=classify(code,start)
    if len(calls)>24:
        raise ValueError("V90 startup tail call count exceeds limit")
    print(f"V90_TAIL entry=0x{entry:08X} begin=0x{start:08X} end=0x{end:08X}")
    for site,dest in calls:
        print(f"V90_CALL site=0x{site:08X} target=0x{dest:08X} size=0x{funcs.get(dest,0):X}")
    for i,(word,) in enumerate(struct.iter_unpack(">I",code)):
        pc=start+4*i
        if word==0x4e800020:
            print(f"V90_RETURN site=0x{pc:08X}")
        elif word>>26==16:
            disp=word&0xfffc
            if disp&0x8000:disp-=0x10000
            dst=(disp if word&2 else pc+disp)&0xffffffff
            print(f"V90_BRANCH site=0x{pc:08X} target=0x{dst:08X}")
        elif word>>26==18 and not word&1:
            print(f"V90_BRANCH site=0x{pc:08X} target=0x{branch_target(word,pc):08X}")
        elif word>>26==19 and (word>>1)&1023==528:
            print(f"V90_INDIRECT site=0x{pc:08X} link={word&1}")
    return calls

def scan(raw,funcs):
    os_calls=tail(raw,funcs,OSINIT,OS_TAIL)
    start_calls=tail(raw,funcs,ENTRY,START_TAIL)
    if not os_calls or os_calls[0]!=(OS_TAIL,ROOTS[0]):
        raise ValueError("V90 authenticated OSInit frontier differs")
    # Keep the graph finite; inspect the remaining subsystem roots and their
    # immediate descendants, not every game function. Only geometry leaves
    # the private runner, never original code, names, strings or data.
    todo=list(dict.fromkeys(ROOTS+tuple(t for _,t in os_calls)+tuple(t for _,t in start_calls)))
    seen=set()
    for node in todo:
        if len(seen)>=MAX_NODES:break
        if node in seen or not 0<funcs.get(node,0)<=MAX_SIZE:continue
        # A very large direct-call census is not required at this boundary.
        code=get_text(raw,node,funcs[node])
        _,calls=classify(code,node)
        if len(calls)>24:continue
        seen.add(node)
        describe(raw,funcs,node)
    for node in ROOTS:
        size=funcs.get(node,0)
        if not 0<size<=MAX_SIZE:raise ValueError("V90 named frontier missing")
        for i,(word,) in enumerate(struct.iter_unpack(">I",get_text(raw,node,size))):
            major=word>>26;ra=(word>>16)&31
            if ra in (2,13) and major in (32,34,40,42,36,38,44):
                off=word&0xffff
                if off&0x8000:off-=0x10000
                print(f"V90_SDA func=0x{node:08X} site=0x{node+4*i:08X} base={ra} offset={off} access={'load' if major in (32,34,40,42) else 'store'}")
    print("PASS: bounded authenticated OSInit and startup continuation metadata")

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("dol",type=Path)
    p.add_argument("elf",type=Path)
    a=p.parse_args()
    raw=a.dol.read_bytes();elf=a.elf.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=ORIGINAL_SHA or hashlib.sha256(elf).hexdigest()!=ORIGINAL_SHA256:
        raise ValueError("owner digest mismatch")
    scan(raw,parse_functions(elf))
