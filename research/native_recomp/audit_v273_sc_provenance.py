#!/usr/bin/env python3
"""V273: bounded straight-line PowerPC value provenance for SYSCONF stores.

Private SHA-verified original Wii ELF only. Propagates a byte value
through li/lis, addi, ori, mr, and relevant loads. Stops at control-flow
edges and unsupported writers. A static candidate is not evidence of
guest execution, and no proprietary instruction words are emitted.
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

WRITERS=(0x8052f790,0x8052f830,0x8052f94c,0x8052fca4,0x80530ba0,0x80530dbc)
CATEGORIES=("c0","c1","c2","c3","cother","status","load","unknown")
MAX_STEPS=32

def signed16(imm:int)->int:
    return (imm ^ 0x8000)-0x8000

def resolve(words:list[int],store_index:int,reg:int,
            limit:int=MAX_STEPS)->tuple[str,int]:
    """Return ("const", byte), ("status", -1), ("load", -1), or unknown.

    Only the low byte matters for stb. Source tracking never crosses a
    branch, exception, or unrecognized instruction that may clobber a GPR.
    """
    if not 0<=reg<32 or not 0<store_index<=len(words) or not 0<limit<=64:
        raise ValueError("geometry")
    def lookup(index:int,target:int,budget:int)->tuple[str,int]:
        if budget<=0:return "unknown",-1
        while index>0 and budget>0:
            index-=1
            budget-=1
            word=words[index]
            op=word>>26
            rt=(word>>21)&31
            ra=(word>>16)&31
            rb=(word>>11)&31
            imm=word&0xffff
            if op in (16,18,19,17):
                return "unknown",-1
            if op in (14,15):
                if target!=rt:continue
                if ra==0:
                    result=signed16(imm)
                    if op==15:result<<=16
                    return "const",result&255
                kind,prior=lookup(index,ra,budget)
                if kind!="const":return "unknown",-1
                return "const",(prior + (signed16(imm) if op==14 else 0))&255
            if op in (32,33,34,35,40,41,42,43):
                if target!=rt:continue
                return ("status",-1) if access(word)=="byte_read" else ("load",-1)
            if op in (24,25,26,27,28,29):
                if target!=ra:continue
                if op==24 and rt==ra and imm==0:
                    continue  # ori r0,r0,0 / other identity NOP
                if op==27 or op==25: # high half unchanged in low byte
                    return lookup(index,rt,budget)
                if op==29:
                    return "const",0  # andis. clears low byte
                kind,prior=lookup(index,rt,budget)
                if kind!="const":
                    if op==28 and (imm&255)==0:
                        return "const",0
                    return "unknown",-1
                if op==24:val=prior | (imm&255)
                elif op==26:val=prior ^ (imm&255)
                elif op==28:val=prior & (imm&255)
                else:return "unknown",-1
                return "const",val
            if op in (10,11,36,37,38,39,44,45):
                continue  # CR update or a non-updating store
            if op in (20,21,23):
                if target==ra:return "unknown",-1
                continue
            if op==31:
                xo=(word>>1)&1023
                if xo in (0,32):continue  # CR compares, no GPR changes
                if xo==444:
                    if target!=ra:continue
                    if rt!=rb:return "unknown",-1
                    return lookup(index,rt,budget)  # mr rA,rS
                return "unknown",-1
            if op in (7,8,12,13):
                if target==rt:return "unknown",-1
                continue
            return "unknown",-1
        return "unknown",-1
    return lookup(store_index,reg,limit)


def classify_function(start:int,words:list[int])->Counter:
    if start&3 or not 1<=len(words)<=8192:
        raise ValueError("geometry")
    result=Counter()
    for i,word in enumerate(words):
        if access(word)!="byte_write":continue
        reg=(word>>21)&31
        kind,val=resolve(words,i,reg)
        if kind=="const":
            key=f"c{val}" if val in (0,1,2,3) else "cother"
        else:
            key=kind
        result[key]+=1
    return result


def audit(data:bytes)->list[str]:
    if hashlib.sha256(data).hexdigest()!=ORIGINAL_SHA256:
        raise ValueError("digest")
    functions=parse_functions(data)
    if len(functions)<25000:
        raise ValueError("symbols")
    groups={}
    for pc in WRITERS:
        n=functions.get(pc,0)
        if n<16 or n>32768 or n%4:
            raise ValueError("function_bounds")
        groups[pc]=classify_function(pc,read_words(data,pc,n//4))
    totals=Counter()
    for value in groups.values():totals.update(value)
    if sum(totals.values())!=11 or sum(groups[0x8052f830].values())!=2:
        raise ValueError("source_sites")
    rows=["V273_SC_PROVENANCE owners=6 stores=11 "+
          " ".join(f"{k}={totals[k]}" for k in CATEGORIES)]
    for pc,counts in sorted(groups.items()):
        rows.append(f"V273_OWNER pc={pc:08x} stores={sum(counts.values())} "+
                    " ".join(f"{k}={counts[k]}" for k in CATEGORIES))
    return rows


def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_owner_elf",type=Path)
    a=p.parse_args()
    try: result=audit(a.private_owner_elf.read_bytes())
    except (ValueError,OSError):
        print("V273_PROVENANCE_AUDIT verified=0",file=sys.stderr)
        return 1
    print("V273_PROVENANCE_AUDIT verified=1")
    print("\n".join(result))
    return 0

if __name__=="__main__":
    sys.exit(main())
