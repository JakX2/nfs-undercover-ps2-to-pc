#!/usr/bin/env python3
"""V277 owner Wii ELF: direct PowerPC BL callers of SC writer functions.

Only SHA-verified original Wii executable read from private CI.
Direct BL edges are callgraph evidence, not proof of callback execution.
Indirect bctrl/blr, calls through import stubs or function pointers
are outside this audit; instruction bytes are never printed.
"""
from __future__ import annotations
import argparse
from collections import Counter,defaultdict
import hashlib
from pathlib import Path
import struct
import sys
from audit_v243_original_callback_branch import branch_target
from audit_v268_sc_status_writers import owners
from make_private_elf_symbol_map import HEADER,SECTION,ORIGINAL_SHA256,parse_functions

TARGETS=(0x8052f790,0x8052f830,0x8052f94c,
         0x8052fca4,0x80530ba0,0x80530dbc)

def find_calls(words:list[int],base:int,targets:tuple[int,...]=TARGETS
               )->list[tuple[int,int]]:
    if base&3 or len(words)>4000000:
        raise ValueError("geometry")
    wanted=set(targets)
    result=[]
    for i,word in enumerate(words):
        if word>>26!=18 or not(word&1):continue
        pc=base+4*i
        dest=branch_target(pc,word)
        if dest in wanted:
            result.append((pc,dest))
    return result


def classify(calls:list[tuple[int,int]],functions:dict[int,int])->list[str]:
    mapped=owners([(pc,"call") for pc,_ in calls],functions)
    by_target=defaultdict(Counter)
    for (pc,target),(caller,_) in zip(calls,mapped):
        by_target[target][caller]+=1
    unique={(target,owner) for target,cnt in by_target.items() for owner in cnt}
    writer_to_writer=sum(n for target,cnt in by_target.items()
                         for owner,n in cnt.items() if owner in TARGETS)
    rows=[f"V277_SC_CALLS targets=6 direct_calls={len(calls)} "
          f"caller_pairs={len(unique)} writer_to_writer={writer_to_writer} "
          f"unmapped={sum(x==0 for x,_ in mapped)}"]
    for target in TARGETS:
        counts=by_target[target]
        rows.append(f"V277_SC_TARGET target={target:08x} "
                    f"calls={sum(counts.values())} callers={len(counts)}")
        for rank,(caller,count) in enumerate(
            sorted(counts.items(),key=lambda v:(-v[1],v[0]))[:6],1):
            rows.append(f"V277_SC_CALLER target={target:08x} "
                        f"rank={rank} owner={caller:08x} calls={count}")
    return rows


def audit(data:bytes)->list[str]:
    if hashlib.sha256(data).hexdigest()!=ORIGINAL_SHA256:
        raise ValueError("digest")
    funcs=parse_functions(data)
    if len(funcs)<25000 or any(t not in funcs for t in TARGETS):
        raise ValueError("symbols")
    header=HEADER.unpack_from(data)
    off,unit,n=header[6],header[11],header[12]
    if unit!=SECTION.size or not 0<n<10000 or off+n*unit>len(data):
        raise ValueError("sections")
    calls=[]
    sections=0
    for ix in range(n):
        _,kind,flags,base,pos,size,*_=SECTION.unpack_from(data,off+ix*unit)
        if kind==8 or not(flags&4):continue
        if base&3 or pos&3 or size&3 or not 0<size<=16*1024*1024 or pos+size>len(data):
            raise ValueError("section_bounds")
        sections+=1
        calls.extend(find_calls(
            (v[0] for v in struct.iter_unpack(">I",data[pos:pos+size]))
            if False else [v[0] for v in struct.iter_unpack(">I",data[pos:pos+size])],
            base))
    if not 0<sections<=32:raise ValueError("sections")
    return classify(calls,funcs)


def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("owner_elf",type=Path)
    a=p.parse_args()
    try: rows=audit(a.owner_elf.read_bytes())
    except (OSError,ValueError):
        print("V277_SC_CALL_AUDIT verified=0",file=sys.stderr)
        return 1
    print("V277_SC_CALL_AUDIT verified=1")
    print("\n".join(rows))
    return 0

if __name__=="__main__":
    sys.exit(main())
