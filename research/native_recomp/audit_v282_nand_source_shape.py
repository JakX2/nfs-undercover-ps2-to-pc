#!/usr/bin/env python3
"""V282 static structure of original Wii 0x8051E150 NAND result producer.

This function's output guards the call to original SC writer 0x8052FCA4.
Only authenticated original ELF is inspected, and only bounded control
flow counts/function addresses leave the owner-private CI.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
from pathlib import Path
import sys

from audit_v243_original_callback_branch import branch_target
from audit_v264_osinit_retry_elf import read_words
from audit_v268_sc_status_writers import access
from make_private_elf_symbol_map import ORIGINAL_SHA256,parse_functions

FUNC=0x8051e150
SC_OFFSET=(-3176)&0xffff

def analyze_words(words:list[int],pc:int=FUNC)->list[str]:
    if pc!=FUNC or not 4<=len(words)<=8192:
        raise ValueError("geometry")
    call_targets=Counter()
    ret=0
    literal_returns=Counter()
    branches=0
    sda_read=sda_write=0
    field188_read=field188_write=0
    for i,w in enumerate(words):
        op=w>>26
        xo=(w>>1)&1023
        if op==16:branches+=1
        if op==18 and w&1:
            dest=branch_target(pc+4*i,w)
            if dest is not None:call_targets[dest]+=1
        if op==19 and xo==16:
            ret+=1
            if i:
                prior=words[i-1]
                if ((prior>>26)==14 and (prior>>21)&31==3
                        and (prior>>16)&31==0):
                    v=prior&0xffff
                    literal_returns[v if v in (0,1,2,3) else 4]+=1
        kind=access(w)
        if kind=="byte_read":sda_read+=1
        if kind=="byte_write":sda_write+=1
        if (w&0xffff)==0x188 and ((w>>16)&31)!=0:
            if op==32:field188_read+=1
            if op in (36,38,44):field188_write+=1
    rows=[
        f"V282_SOURCE original=8051e150 instructions={len(words)} "
        f"direct_calls={sum(call_targets.values())} target_count={len(call_targets)} "
        f"cond_branches={branches} bclr={ret} "
        f"literal_return0={literal_returns[0]} literal_return1={literal_returns[1]} "
        f"literal_return2={literal_returns[2]} literal_return3={literal_returns[3]} "
        f"literal_return_other={literal_returns[4]} "
        f"sc_read={sda_read} sc_write={sda_write} "
        f"field188_read={field188_read} field188_write={field188_write}"
    ]
    for rank,(target,n) in enumerate(sorted(
        call_targets.items(),key=lambda kv:(-kv[1],kv[0]))[:8],1):
        rows.append(f"V282_SOURCE_CALL rank={rank} target={target:08x} count={n}")
    return rows


def audit(data:bytes)->list[str]:
    if hashlib.sha256(data).hexdigest()!=ORIGINAL_SHA256:
        raise ValueError("digest")
    funcs=parse_functions(data)
    if len(funcs)<25000:
        raise ValueError("symbols")
    n=funcs.get(FUNC,0)
    if n<16 or n>32768 or n&3:
        raise ValueError("function_bounds")
    return analyze_words(read_words(data,FUNC,n//4))


def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_owner_elf",type=Path)
    a=p.parse_args()
    try: lines=audit(a.private_owner_elf.read_bytes())
    except (OSError,ValueError):
        print("V282_SOURCE_AUDIT verified=0",file=sys.stderr)
        return 1
    print("V282_SOURCE_AUDIT verified=1")
    print("\n".join(lines))
    return 0

if __name__=="__main__":
    sys.exit(main())
