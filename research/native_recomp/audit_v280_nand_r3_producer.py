#!/usr/bin/env python3
"""V280 owner Wii ELF: trace original NAND child r3 before guarded writer.

Validate V279's exact original conditional branch, then trace local
straight-line r3 definitions to a direct BL return, memory load,
constant, or conservative unknown. No original instruction words,
translated game source or private registers are emitted.
"""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import sys

from audit_v243_original_callback_branch import branch_target
from audit_v264_osinit_retry_elf import read_words
from audit_v279_nand_writer_guard import CHILD,WRITER,classify as guard_classify
from make_private_elf_symbol_map import ORIGINAL_SHA256,parse_functions

MAX_BACK=40
LOAD_OPS=(32,33,34,35,40,41,42,43)

def signed16(x:int)->int:
    return (x^0x8000)-0x8000

def trace_source(words:list[int],before:int,reg:int=3)->dict[str,int|str]:
    if not 0<before<=len(words) or not 0<=reg<32:
        raise ValueError("geometry")
    at=before
    copies=0
    def item(kind:str,ix:int,target:int=0,width:int=0,base:int=-1,
             disp:int=0)->dict[str,int|str]:
        return dict(kind=kind,offset=ix*4,target=target,tracked=reg,
                    width=width,base=base,disp=disp,copies=copies)
    for _ in range(MAX_BACK):
        if at<=0:break
        at-=1
        w=words[at]
        op=w>>26
        rt=(w>>21)&31
        ra=(w>>16)&31
        rb=(w>>11)&31
        imm=w&0xffff
        if op==18:
            if w&1:
                return item("call",at,branch_target(CHILD+4*at,w) or 0)
            return item("barrier",at)
        if op in (16,17,19):return item("barrier",at)
        if op in LOAD_OPS:
            if rt!=reg:continue
            width=1 if op in (34,35) else 2 if op in (40,41,42,43) else 4
            return item("load",at,width=width,base=ra,disp=signed16(imm))
        if op in (14,15):
            if rt!=reg:continue
            if ra==0:
                return item("immediate",at,target=(signed16(imm)&255))
            return item("computed",at)
        if op in (24,25,26,27,28,29):
            if ra!=reg:continue
            if op in (24,25) and imm==0:
                reg=rt
                copies+=1
                continue
            return item("computed",at)
        if op==31:
            xo=(w>>1)&1023
            if xo in (0,32):continue
            if xo==444 and ra==reg and rt==rb:
                reg=rt
                copies+=1
                continue
            if xo==444 and ra!=reg:continue
            return item("unknown",at)
        if op in (10,11,36,37,38,39,44,45):continue
        if op in (20,21,23):
            if ra==reg:return item("computed",at)
            continue
        return item("unknown",at)
    return item("entry",-1)


def classify(words:list[int])->str:
    guard=guard_classify(words,CHILD)
    if guard["call_offset"]!=184 or guard["nearest_skip_offset"]!=180 or (
        guard["producer_kind"]!=1 or guard["producer_ra"]!=3 or
        guard["producer_imm_class"]!=0):
        raise ValueError("verified_guard")
    cmpidx=guard["nearest_skip_offset"]//4-1
    src=trace_source(words,cmpidx,3)
    return (
        f"V280_NAND_R3 child=8052fa60 writer=8052fca4 "
        f"cmp_offset={cmpidx*4} guarded_call={guard['call_offset']} "
        f"guards={guard['skip_cond']} source={src['kind']} "
        f"source_offset={src['offset']} source_target={src['target']:08x} "
        f"tracked={src['tracked']} copies={src['copies']} "
        f"width={src['width']} base={src['base']} disp={src['disp']}"
    )


def audit(data:bytes)->str:
    if hashlib.sha256(data).hexdigest()!=ORIGINAL_SHA256:
        raise ValueError("digest")
    funcs=parse_functions(data)
    if len(funcs)<25000 or WRITER not in funcs:
        raise ValueError("symbols")
    n=funcs.get(CHILD,0)
    if n<32 or n>32768 or n%4:raise ValueError("geometry")
    return classify(read_words(data,CHILD,n//4))


def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("owner_elf",type=Path)
    a=p.parse_args()
    try: result=audit(a.owner_elf.read_bytes())
    except (OSError,ValueError):
        print("V280_R3_AUDIT verified=0",file=sys.stderr)
        return 1
    print("V280_R3_AUDIT verified=1")
    print(result)
    return 0

if __name__=="__main__":
    sys.exit(main())
