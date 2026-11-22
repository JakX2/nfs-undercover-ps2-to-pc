#!/usr/bin/env python3
"""V268 private original Wii ELF: find direct SDA SYSCONF status writers.

Search all executable ELF sections for *direct* r13-3176 loads/stores.
This cannot see indexed/pointer-mediated accesses and never proves a
writer executes in the current callback path. Publish only owner PCs,
access categories, counts; never code words or guest data bytes.
"""
from __future__ import annotations

import argparse
from bisect import bisect_right
from collections import Counter
import hashlib
from pathlib import Path
import struct
import sys

from make_private_elf_symbol_map import (
    HEADER, SECTION, ORIGINAL_SHA256, parse_functions,
)

STATUS_DISP=(-3176)&0xffff
HELPER=0x8052f830
LOADS=(32,33,34,35,40,41,42,43)
STORES=(36,37,38,39,44,45)
BYTE_READ=34
BYTE_WRITE=38


def access(word:int)->str:
    """Only absolute displacement relative to r13, not indirect aliases."""
    op=word>>26
    if (word>>16)&31!=13 or (word&0xffff)!=STATUS_DISP:
        return "other"
    if op==BYTE_READ:
        return "byte_read"
    if op==BYTE_WRITE:
        return "byte_write"
    if op in LOADS:
        return "wide_read"
    if op in STORES:
        return "wide_write"
    return "other"


def scan(words:list[int],base:int)->list[tuple[int,str]]:
    if base&3 or len(words)>4000000:
        raise ValueError("geometry")
    return [(base+4*i,k) for i,w in enumerate(words)
            if (k:=access(w))!="other"]


def owners(accesses:list[tuple[int,str]],
           functions:dict[int,int])->list[tuple[int,str]]:
    starts=sorted(functions)
    ret=[]
    for pc,kind in accesses:
        idx=bisect_right(starts,pc)-1
        if idx<0:
            ret.append((0,kind))
            continue
        owner=starts[idx]
        ret.append((owner if pc<owner+functions[owner] else 0,kind))
    return ret


def audit(data:bytes)->tuple[dict[str,int],list[tuple[int,str]]]:
    if hashlib.sha256(data).hexdigest()!=ORIGINAL_SHA256:
        raise ValueError("digest")
    functions=parse_functions(data)
    if len(functions)<25000 or HELPER not in functions:
        raise ValueError("symbols")
    header=HEADER.unpack_from(data)
    off,unit,n=header[6],header[11],header[12]
    if unit!=SECTION.size or not 0<n<10000 or off+n*unit>len(data):
        raise ValueError("sections")
    found=[]
    sections=0
    for i in range(n):
        _,kind,flags,base,pos,size,*_=SECTION.unpack_from(data,off+i*unit)
        if not flags&4 or kind==8:
            continue
        if (base&3 or pos&3 or size&3 or not 0<size<=16*1024*1024
                or pos+size>len(data)):
            raise ValueError("geometry")
        sections+=1
        words=[w[0] for w in struct.iter_unpack(">I",data[pos:pos+size])]
        found.extend(scan(words,base))
    if not 0<sections<=32:
        raise ValueError("sections")
    grouped=owners(found,functions)
    kinds=Counter(kind for _,kind in grouped)
    writer_owners={pc for pc,k in grouped if "write" in k}
    stats={
        "sections":sections,
        "read":kinds["byte_read"]+kinds["wide_read"],
        "write":kinds["byte_write"]+kinds["wide_write"],
        "byte_read":kinds["byte_read"],
        "byte_write":kinds["byte_write"],
        "helper_read":sum(pc==HELPER and "read" in k for pc,k in grouped),
        "helper_write":sum(pc==HELPER and "write" in k for pc,k in grouped),
        "writer_owners":len(writer_owners),
        "unmapped":sum(pc==0 for pc,_ in grouped),
    }
    return stats,grouped


def sanitized(stats:dict[str,int], grouped:list[tuple[int,str]])->list[str]:
    keys=("sections","read","write","byte_read","byte_write",
          "helper_read","helper_write","writer_owners","unmapped")
    rows=["V268_SC_DIRECT "+" ".join(f"{k}={stats[k]}" for k in keys)]
    counts=Counter(pc for pc,kind in grouped if "write" in kind)
    for rank,(pc,n) in enumerate(
        sorted(counts.items(),key=lambda t:(-t[1],t[0]))[:8],1):
        rows.append(f"V268_SC_WRITER rank={rank} owner={pc:08x} writes={n}")
    return rows


def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_elf",type=Path)
    a=p.parse_args()
    try: stats,details=audit(a.private_elf.read_bytes())
    except (OSError,ValueError):
        print("V268_SC_AUDIT verified=0",file=sys.stderr)
        return 1
    print("V268_SC_AUDIT verified=1")
    print("\n".join(sanitized(stats,details)))
    return 0


if __name__=="__main__":
    sys.exit(main())
