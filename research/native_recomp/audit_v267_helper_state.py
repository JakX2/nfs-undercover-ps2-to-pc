#!/usr/bin/env python3
"""V267: SHA-pinned original Wii 0x8052F830 helper-state audit.

Read only original PowerPC ELF instructions inside the verified function.
Emit coarse counters, never words/bytes/disassembly, symbol names or raw
memory. Presence of a code pattern is not proof the native path executed it.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import sys

from audit_v264_osinit_retry_elf import (
    HELPER, DISABLE, RESTORE, GETTIME, read_words
)
from audit_v243_original_callback_branch import branch_target
from make_private_elf_symbol_map import ORIGINAL_SHA256, parse_functions

LOADS=(32,33,34,35,40,41,42,43)
SC_OFFSET=(-3176)&0xffff


def classify(pc:int,words:list[int])->dict[str,int]:
    if (pc!=HELPER or not 8<=len(words)<=8192):
        raise ValueError("geometry")
    values=[{"op":w>>26,"rd":(w>>21)&31,
             "ra":(w>>16)&31,"imm":w&0xffff,
             "word":w} for w in words]
    nested=[branch_target(pc+4*i,w) for i,w in enumerate(words)]
    def sda(v):
        return v["op"] in LOADS and v["ra"]==13
    def sc(v):
        return sda(v) and v["imm"]==SC_OFFSET
    def literal(v):
        return v["op"]==14 and v["rd"]==3 and v["ra"]==0
    # A blr-form is counted, but its dynamic reachability is *not* inferred.
    lr_br=[v for v in values
           if v["op"]==19 and ((v["word"]>>1)&1023)==16]
    return {
        "size_ins":len(words),
        "direct_calls":sum(w>>26==18 and bool(w&1) for w in words),
        "disable":sum(t==DISABLE for t in nested),
        "restore":sum(t==RESTORE for t in nested),
        "gettime":sum(t==GETTIME for t in nested),
        "mftb":sum(v["op"]==31 and ((v["word"]>>1)&1023)==371 for v in values),
        "sda_loads":sum(map(sda,values)),
        "sc_direct":sum(map(sc,values)),
        "sc_byte":sum(sc(v) and v["op"]==34 for v in values),
        "sda_other":sum(sda(v) and not sc(v) for v in values),
        "lr_branch":len(lr_br),
        "blr_unconditional":sum(((v["word"]>>21)&31)==20 and
                                not(v["word"]&1) for v in lr_br),
        "r3_li_one":sum(literal(v) and v["imm"]==1 for v in values),
        "r3_li_zero":sum(literal(v) and v["imm"]==0 for v in values),
        "r3_li_other":sum(literal(v) and v["imm"] not in (0,1) for v in values),
        "r3_load":sum(v["op"] in LOADS and v["rd"]==3 for v in values),
        "r3_or_copy":sum(v["op"]==31 and ((v["word"]>>1)&1023)==444
                         and v["ra"]==3 and
                         ((v["word"]>>21)&31)==((v["word"]>>11)&31)
                         for v in values),
        "cmp_r3_one":sum(v["op"] in (10,11) and v["ra"]==3
                          and v["imm"]==1 for v in values),
    }


def audit(data:bytes)->dict[str,int]:
    if hashlib.sha256(data).hexdigest()!=ORIGINAL_SHA256:
        raise ValueError("digest")
    functions=parse_functions(data)
    if len(functions)<25000:
        raise ValueError("symbols")
    size=functions.get(HELPER,0)
    if size<32 or size>32768 or size%4:
        raise ValueError("helper")
    return classify(HELPER,read_words(data,HELPER,size//4))


def sanitized(v:dict[str,int])->str:
    fields=("size_ins","direct_calls","disable","restore","gettime","mftb",
            "sda_loads","sc_direct","sc_byte","sda_other","lr_branch",
            "blr_unconditional","r3_li_one","r3_li_zero","r3_li_other",
            "r3_load","r3_or_copy","cmp_r3_one")
    return "V267_HELPER_STATE "+" ".join(f"{x}={v[x]}" for x in fields)


def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("owner_elf",type=Path)
    a=p.parse_args()
    try: result=audit(a.owner_elf.read_bytes())
    except (OSError,ValueError):
        print("V267_HELPER_AUDIT verified=0",file=sys.stderr)
        return 1
    print("V267_HELPER_AUDIT verified=1")
    print(sanitized(result))
    return 0


if __name__=="__main__":
    sys.exit(main())
