#!/usr/bin/env python3
"""Bounded, original-free metadata planner for the post-V68 startup calls."""
import argparse,hashlib,struct
from pathlib import Path
from make_hardware_boundary_v17 import ORIGINAL_SHA,get_text
from make_private_elf_symbol_map import ORIGINAL_SHA256,parse_functions
from probe_next_osinit_v33 import classify,branch_target
CALLSITE=0x80520948
ROOT=0x805194c4
MAX_SIZE=0x1000
MAX_EDGES=24

def describe(raw,functions,addr):
    size=functions.get(addr,0)
    if not 0<size<=MAX_SIZE or size%4:
        raise ValueError("missing or unbounded ELF function span")
    code=get_text(raw,addr,size)
    counts,calls=classify(code,addr)
    if len(calls)>MAX_EDGES:raise ValueError("too many direct edges")
    print(f"POST68_FUNCTION addr=0x{addr:08X} size=0x{size:X} calls={len(calls)} branches={counts['conditional_branches']+counts['direct_branches']}")
    for pc,dst in calls:
        print(f"POST68_EDGE site=0x{pc:08X} target=0x{dst:08X} size=0x{functions.get(dst,0):X}")
    # No opcodes or disassembly: count return sites and indirect branch classes.
    words=struct.iter_unpack(">I",code)
    ret=indirect=0
    for (op,) in words:
        if op==0x4e800020:ret+=1
        elif op>>26==19 and (op>>1)&1023 in (16,528):indirect+=1
    print(f"POST68_TERMINALS addr=0x{addr:08X} returns={ret} indirect={indirect}")
    return calls

def main():
    p=argparse.ArgumentParser();p.add_argument("dol",type=Path);p.add_argument("elf",type=Path);a=p.parse_args()
    raw=a.dol.read_bytes();elf=a.elf.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=ORIGINAL_SHA or hashlib.sha256(elf).hexdigest()!=ORIGINAL_SHA256:
        raise ValueError("owner digest mismatch")
    op=struct.unpack(">I",get_text(raw,CALLSITE,4))[0]
    if op&3!=1 or branch_target(op,CALLSITE)!=ROOT:raise ValueError("original frontier call changed")
    funcs=parse_functions(elf)
    calls=describe(raw,funcs,ROOT)
    for dst in dict.fromkeys(t for _,t in calls):
        if dst!=ROOT and 0<funcs.get(dst,0)<=MAX_SIZE:
            describe(raw,funcs,dst)
    print("PASS: bounded authenticated post-V68 call graph")
if __name__=="__main__":main()
