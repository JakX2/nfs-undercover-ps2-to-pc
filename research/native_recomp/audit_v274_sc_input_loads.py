#!/usr/bin/env python3
"""V274: original Wii SYSCONF-store input load sites, SHA-pinned owner only.

Conservatively walk backward from each of six direct stores across three
remaining writer functions, through only exact copies/identity operations.
Report input load widths, base register categories and displacements.
A static load-to-store path is not proof that a callback ran or a value
of 3 was ever produced; original game instructions remain private.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
from pathlib import Path
import sys

from audit_v264_osinit_retry_elf import read_words
from audit_v268_sc_status_writers import access
from make_private_elf_symbol_map import ORIGINAL_SHA256, parse_functions

TARGETS=(0x8052fca4,0x80530ba0,0x80530dbc)
LOAD_OPS=(32,33,34,35,40,41,42,43)
STATUS_OFFSET=(-3176)&0xffff
BRANCHES=(16,17,18,19)
MAX_WALK=32


def signed16(x:int)->int:
    return (x ^ 0x8000) - 0x8000


def classify_source(words:list[int],store_at:int,reg:int)->tuple[str,str,str,int,int,int]:
    """(kind, width, base_kind, disp, source_offset, copies).

    Stop at control-flow edges and unfamiliar register definitions.
    """
    if not 0<=reg<32 or not 0<store_at<=len(words):
        raise ValueError("geometry")
    idx=store_at
    copies=0
    for _ in range(MAX_WALK):
        if idx<=0:break
        idx-=1
        word=words[idx]
        op=word>>26
        rt=(word>>21)&31
        ra=(word>>16)&31
        rb=(word>>11)&31
        imm=word&0xffff
        if op in BRANCHES:
            return "branch","none","none",0,-1,copies
        if op in LOAD_OPS:
            if rt!=reg:continue
            width=("byte" if op in (34,35) else
                   "half" if op in (40,41,42,43) else "word")
            base=("absolute" if ra==0 else "stack" if ra==1 else
                  "sda" if ra==13 else "pointer")
            kind=("status" if op==34 and ra==13 and imm==STATUS_OFFSET
                  else "load")
            return kind,width,base,signed16(imm),idx*4,copies
        if op in (14,15):
            if rt!=reg:continue
            if ra==0:
                return "constant","none","none",signed16(imm)&255,idx*4,copies
            return "computed","none","none",0,idx*4,copies
        if op in (24,25,26,27,28,29):
            if ra!=reg:continue
            if op in (24,25) and imm==0:
                reg=rt
                copies+=1
                continue
            return "computed","none","none",0,idx*4,copies
        if op==31:
            xo=(word>>1)&1023
            if xo in (0,32):continue
            if xo==444 and ra==reg and rt==rb:
                reg=rt
                copies+=1
                continue
            if xo==444 and ra!=reg:continue
            return "unknown","none","none",0,idx*4,copies
        if op in (10,11,36,37,38,39,44,45):continue
        if op in (20,21,23):
            if ra==reg:return "computed","none","none",0,idx*4,copies
            continue
        if op in (7,8,12,13):
            if rt==reg:return "computed","none","none",0,idx*4,copies
            continue
        return "unknown","none","none",0,idx*4,copies
    return "entry","none","none",0,-1,copies


def classify_function(pc:int,words:list[int])->list[str]:
    if pc&3 or len(words)<8 or len(words)>8192:
        raise ValueError("geometry")
    rows=[]
    for i,word in enumerate(words):
        if access(word)!="byte_write":continue
        rs=(word>>21)&31
        kind,width,base,disp,origin,hops=classify_source(words,i,rs)
        rows.append(
            f"V274_INPUT owner={pc:08x} store_offset={i*4} "
            f"kind={kind} width={width} base={base} disp={disp} "
            f"source_offset={origin} copies={hops}")
    return rows


def audit(data:bytes)->list[str]:
    if hashlib.sha256(data).hexdigest()!=ORIGINAL_SHA256:
        raise ValueError("digest")
    functions=parse_functions(data)
    if len(functions)<25000:raise ValueError("symbols")
    rows=[]
    for pc in TARGETS:
        n=functions.get(pc,0)
        if n<32 or n>32768 or n%4:
            raise ValueError("function_bounds")
        result=classify_function(pc,read_words(data,pc,n//4))
        if len(result)!={TARGETS[0]:1,TARGETS[1]:3,TARGETS[2]:2}[pc]:
            raise ValueError("writer_count")
        rows.extend(result)
    if len(rows)!=6:raise ValueError("writer_count")
    kinds=Counter(line.split("kind=",1)[1].split(" ",1)[0] for line in rows)
    return [
        f"V274_INPUT_SUMMARY owners=3 stores=6 load={kinds['load']} "
        f"status={kinds['status']} constant={kinds['constant']} "
        f"computed={kinds['computed']} unknown={kinds['unknown']} "
        f"branch={kinds['branch']} entry={kinds['entry']}"
    ]+rows


def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_owner_elf",type=Path)
    a=p.parse_args()
    try: lines=audit(a.private_owner_elf.read_bytes())
    except (OSError,ValueError):
        print("V274_INPUT_AUDIT verified=0",file=sys.stderr)
        return 1
    print("V274_INPUT_AUDIT verified=1")
    print("\n".join(lines))
    return 0

if __name__=="__main__":
    sys.exit(main())
