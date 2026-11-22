#!/usr/bin/env python3
"""V324: SHA-authenticated original Wii callgraph of five NAND descendants.

The prior V312 helper at 0x80519BCC calls these five exact or interior
targets. Read only their bounded ELF symbol windows, not an invented full
function for an interior branch. Export addresses and instruction classes,
never proprietary words, disassembly or source snippets.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
from pathlib import Path
import sys

from audit_v243_original_callback_branch import branch_target
from audit_v264_osinit_retry_elf import read_words
from make_private_elf_symbol_map import ORIGINAL_SHA256,parse_functions
from resolve_v308_descendant_boundaries import resolve

TARGETS=(0x805195EC,0x8051AD38,0x80522294,0x80545100,0x8054514C)

def analyze_word_window(pc:int, words:list[int])->tuple[int,int,int,int,int,Counter[int]]:
    if not words or len(words)>8192 or any(not 0<=word<=0xFFFFFFFF for word in words):
        raise ValueError("word_geometry")
    cond=local=bclr=bcctr=conditional_calls=0
    calls=Counter()
    for index,word in enumerate(words):
        op=word>>26
        xo=(word>>1)&1023
        addr=pc+4*index
        if op==16:
            cond+=1
            if word&1:
                conditional_calls+=1
                dest=branch_target(addr,word)
                if dest is not None:
                    calls[dest]+=1
        elif op==18:
            dest=branch_target(addr,word)
            if dest is None:
                raise ValueError("branch_decode")
            if word&1:
                calls[dest]+=1
            elif pc<=dest<pc+len(words)*4:
                local+=1
        elif op==19 and xo==16:
            bclr+=1
        elif op==19 and xo==528:
            bcctr+=1
    return cond,local,bclr,bcctr,conditional_calls,calls

def inspect(data:bytes,*,digest:str=ORIGINAL_SHA256,
            parser=parse_functions,word_reader=read_words)->list[str]:
    if hashlib.sha256(data).hexdigest()!=digest:
        raise ValueError("authenticated_digest")
    funcs=parser(data)
    rows=[]
    exact=interior=unknown=direct_calls=0
    for pc in TARGETS:
        window=resolve(funcs,pc)
        if not window.length:
            unknown+=1
            rows.append(
                f"V324_FLOW pc={pc:08x} kind={window.kind} words=0 "
                f"calls=0 targets=0 cond=0 local=0 bclr=0 bcctr=0 conditional_calls=0"
            )
            continue
        words=word_reader(data,pc,window.length//4)
        if len(words)!=window.length//4:
            raise ValueError("original_window")
        cond,local,bclr,bcctr,cond_calls,calls=analyze_word_window(pc,words)
        exact+=int(window.kind=="exact")
        interior+=int(window.kind=="interior")
        direct_calls+=sum(calls.values())
        rows.append(
            f"V324_FLOW pc={pc:08x} kind={window.kind} "
            f"words={len(words)} calls={sum(calls.values())} "
            f"targets={len(calls)} cond={cond} local={local} bclr={bclr} "
            f"bcctr={bcctr} conditional_calls={cond_calls}"
        )
        for rank,(target,count) in enumerate(sorted(
            calls.items(),key=lambda x:(-x[1],x[0])
        )[:16],1):
            rows.append(
                f"V324_CALLEE from={pc:08x} rank={rank} to={target:08x} calls={count}"
            )
    return [
        f"V324_NAND_FLOW owner=1 targets={len(TARGETS)} exact={exact} "
        f"interior={interior} unknown={unknown} calls={direct_calls}"
    ]+rows

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("owner_private_elf",type=Path)
    a=p.parse_args()
    try:
        rows=inspect(a.owner_private_elf.read_bytes())
    except (OSError,ValueError,IndexError):
        print("V324_ELF_AUDIT verified=0",file=sys.stderr)
        return 1
    print("\n".join(rows))
    print("V324_ELF_AUDIT verified=1")
    return 0

if __name__=="__main__":
    sys.exit(main())
