#!/usr/bin/env python3
"""V272 owner Wii ELF: identify direct writers of SYSCONF status value 3.

For each original r13-3176 byte store, classify only its immediately
preceding instruction as a constant source, load, copy or unknown.
A statically present constant is NOT evidence of an executed callback.
Only function addresses and summary counts leave private CI.
"""
from __future__ import annotations
import argparse
from collections import Counter,defaultdict
import hashlib
from pathlib import Path
import struct
import sys
from audit_v268_sc_status_writers import access,owners
from audit_v270_sc_writer_guards import source_kind
from make_private_elf_symbol_map import (
    HEADER,SECTION,ORIGINAL_SHA256,parse_functions,
)

HELPER=0x8052f830


def classify_sites(sites:list[tuple[int,int,int]],
                   funcs:dict[int,int])->tuple[dict[str,int],list[str]]:
    # (store_pc, source_reg, preceding_PPC_word); preceding word remains private.
    grouped=owners([(pc,"byte_write") for pc,_,_ in sites],funcs)
    allwriters=defaultdict(list)
    for (owner,_),(_,rs,before) in zip(grouped,sites):
        kind,value=source_kind(before,rs)
        category=value if kind==1 else -1
        allwriters[owner].append(category)
    total=len(sites)
    stats={
        "stores":total,
        "owner_count":len(allwriters),
        "const0":sum(0 in [x] for v in allwriters.values() for x in v),
        "const1":sum(x==1 for v in allwriters.values() for x in v),
        "const2":sum(x==2 for v in allwriters.values() for x in v),
        "const3":sum(x==3 for v in allwriters.values() for x in v),
        "const_other":sum(x==4 for v in allwriters.values() for x in v),
        "unknown":sum(x==-1 for v in allwriters.values() for x in v),
        "helper_stores":len(allwriters[HELPER]),
        "helper_one":sum(x==1 for x in allwriters[HELPER]),
        "helper_zero":sum(x==0 for x in allwriters[HELPER]),
    }
    rows=[f"V272_SC_WRITERS "+" ".join(f"{k}={v}" for k,v in stats.items())]
    for owner,values in sorted(allwriters.items()):
        rows.append(
            f"V272_SC_WRITER owner={owner:08x} stores={len(values)} "
            f"c0={values.count(0)} c1={values.count(1)} "
            f"c2={values.count(2)} c3={values.count(3)} "
            f"other={values.count(4)} unknown={values.count(-1)}")
    return stats,rows


def audit(data:bytes)->list[str]:
    if hashlib.sha256(data).hexdigest()!=ORIGINAL_SHA256:
        raise ValueError("digest")
    funcs=parse_functions(data)
    if len(funcs)<25000 or HELPER not in funcs:
        raise ValueError("symbols")
    head=HEADER.unpack_from(data)
    off,unit,n=head[6],head[11],head[12]
    if unit!=SECTION.size or not 0<n<10000 or off+n*unit>len(data):
        raise ValueError("sections")
    sites=[]
    for i in range(n):
        _,kind,flags,addr,pos,size,*_=SECTION.unpack_from(data,off+i*unit)
        if not flags&4 or kind==8:continue
        if (addr&3 or pos&3 or size&3 or
            not 0<size<=16*1024*1024 or pos+size>len(data)):
            raise ValueError("geometry")
        words=[w[0] for w in struct.iter_unpack(">I",data[pos:pos+size])]
        for j,w in enumerate(words):
            if access(w)!="byte_write":continue
            src=(w>>21)&31
            sites.append((addr+4*j,src,words[j-1] if j else 0))
    if len(sites)!=11:
        raise ValueError("original_sites")
    stats,rows=classify_sites(sites,funcs)
    if (stats["owner_count"]!=6 or stats["helper_stores"]!=2 or
        stats["helper_one"]!=1 or stats["helper_zero"]!=1):
        raise ValueError("original_helpers")
    return rows


def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("owner_elf",type=Path)
    a=p.parse_args()
    try: rows=audit(a.owner_elf.read_bytes())
    except (OSError,ValueError):
        print("V272_WRITER_AUDIT verified=0",file=sys.stderr)
        return 1
    print("V272_WRITER_AUDIT verified=1")
    print("\n".join(rows))
    return 0

if __name__=="__main__":
    sys.exit(main())
